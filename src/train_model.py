import torch
import torch.nn as nn
import torch.nn.functional as F
import globals as globals

import numpy as np
import sys
import getopt
import time
import pickle

from train.ordinal_classification_net import OrdinalClassificationNet
from train.binary_classification_net import BinaryClassificationNet
from train.regression_net import RegressionNet
from train.training_utils import create_train_and_val_loaders, DeviceDataLoader, to_device, gen_learning_curve, seed_everything

import rainfall_prediction as rp

# TODO: really compute the weights!
def compute_weights_for_binary_classification(y):
    print(y.shape)
    weights = np.zeros_like(y)

    mask_NORAIN = np.where(y == 0)[0]
    print(mask_NORAIN.shape)

    mask_RAIN = np.where(y > 0)[0]
    print(mask_RAIN.shape)

    weights[mask_NORAIN] = 1
    weights[mask_RAIN] = 1

    print(f"# NO_RAIN records: {len(mask_NORAIN)}")
    print(f"# RAIN records: {len(mask_RAIN)}")
    return weights

def compute_weights_for_ordinal_classification(y):
    weights = np.zeros_like(y)

    mask_weak = np.logical_and(y >= 0, y < 5)
    weights[mask_weak] = 1

    mask_moderate = np.logical_and(y >= 5, y < 25)
    weights[mask_moderate] = 5

    mask_strong = np.logical_and(y >= 25, y < 50)
    weights[mask_strong] = 25

    mask_extreme = np.logical_and(y >= 50, y < 150)
    weights[mask_extreme] = 50

    return weights

def weighted_mse_loss(input, target, weight):
    return (weight * (input - target) ** 2).sum()

class WeightedBCELoss(torch.nn.Module):
    def __init__(self, pos_weight=None, neg_weight=None):
        super(WeightedBCELoss, self).__init__()
        self.pos_weight = pos_weight
        self.neg_weight = neg_weight

    def forward(self, inputs, targets):
        inputs = torch.clamp(inputs,min=1e-7,max=1-1e-7)

        # Apply class weights to positive and negative examples
        if self.pos_weight is not None and self.neg_weight is not None:
            loss = self.neg_weight * (1 - targets) * torch.log(1 - inputs) + self.pos_weight * targets * torch.log(inputs)
        elif self.pos_weight is not None:
            loss = self.pos_weight * targets * torch.log(inputs)
        elif self.neg_weight is not None:
            loss = self.neg_weight * (1 - targets) * torch.log(1 - inputs)
        else:
            loss = F.binary_cross_entropy(inputs, targets, reduction='mean')
        
        return -torch.mean(loss)

    # def forward(self, inputs, targets):
    #     # inputs: batch_size x 1
    #     # targets: batch_size x 1
        
    #     print(f"inputs.shape: {inputs.shape}")
    #     print(f"targets.shape: {targets.shape}")
        
    #     # Calculate the binary cross-entropy loss
    #     loss = F.binary_cross_entropy(inputs, targets, reduction='none')
        
    #     print(f"loss.shape: {loss.shape}")

    #     # Apply class weights to positive and negative examples
    #     if self.pos_weight is not None:
    #         pos_mask = targets.eq(1)
    #         print(f"pos_mask.shape: {pos_mask.shape}")
    #         pos_loss = torch.masked_select(loss, pos_mask)
    #         print(f"pos_loss.shape: {pos_loss.shape}")
    #         pos_loss = pos_loss * self.pos_weight
    #         loss = torch.where(pos_mask, pos_loss, loss)
        
    #     if self.neg_weight is not None:
    #         neg_mask = targets.eq(0)
    #         print(f"neg_mask.shape: {neg_mask.shape}")
    #         neg_loss = torch.masked_select(loss, neg_mask)
    #         print(f"neg_loss.shape: {neg_loss.shape}")
    #         neg_loss = neg_loss * self.neg_weight
    #         print(f"neg_loss.shape: {neg_loss.shape}")
    #         loss = torch.where(neg_mask, neg_loss, loss)
        
    #     return loss.mean()

hyper_params_dics_bc = {
    "N_EPOCHS" : 3500,
    "PATIENCE" : 1000,
    "BATCH_SIZE" : 1024,
    "WEIGHT_DECAY" : 1e-6,
    "LEARNING_RATE" : .3e-3
}

def train(X_train, y_train, X_val, y_val, prediction_task_id, pipeline_id):
    NUM_FEATURES = X_train.shape[2]
    print(f"Input dimensions of the data matrix: {NUM_FEATURES}")

    # model.apply(initialize_weights)

    if prediction_task_id == rp.PredictionTask.ORDINAL_CLASSIFICATION:
        N_EPOCHS = 3500
        PATIENCE = 1000
        BATCH_SIZE = 1024
        WEIGHT_DECAY = 1e-6
        print("- Prediction task: ordinal classification.")
        train_weights = compute_weights_for_ordinal_classification(y_train)
        val_weights = compute_weights_for_ordinal_classification(y_val)
        train_weights = torch.FloatTensor(train_weights)
        val_weights = torch.FloatTensor(val_weights)

        LEARNING_RATE = .3e-6
        loss = weighted_mse_loss
        NUM_CLASSES = 5

        model = OrdinalClassificationNet(in_channels=NUM_FEATURES, num_classes=NUM_CLASSES)

        print(f" - Shape of y_train before encoding: {y_train.shape}")
        y_train = rp.precipitationvalues_to_ordinalencoding(y_train)
        y_val = rp.precipitationvalues_to_ordinalencoding(y_val)
        print(f" - Shape of y_train after encoding: {y_train.shape}")
    elif prediction_task_id == rp.PredictionTask.BINARY_CLASSIFICATION:
        print("- Prediction task: binary classification.")
        train_weights = None
        val_weights = None
        
        N_EPOCHS = hyper_params_dics_bc["N_EPOCHS"]
        PATIENCE = hyper_params_dics_bc["PATIENCE"]
        BATCH_SIZE = hyper_params_dics_bc["BATCH_SIZE"]
        WEIGHT_DECAY = hyper_params_dics_bc["WEIGHT_DECAY"]
        LEARNING_RATE = hyper_params_dics_bc["LEARNING_RATE"]

        # weights = torch.FloatTensor([1.0, 5.0]) 
        loss = nn.BCELoss()
        # loss = WeightedBCELoss(pos_weight=2, neg_weight=1)

        input_dim = (NUM_FEATURES, globals.TIME_WINDOW_SIZE)
        model = BinaryClassificationNet(in_channels=NUM_FEATURES, input_dim=input_dim)

        print(f"(BEFORE) min/max of y_train: {min(y_train)}/{max(y_train)}")
        print(f"(BEFORE) min/max of y_val: {min(y_val)}/{max(y_val)}")
        print(f"(BEFORE) unique of y_train: {np.unique(y_train)}")
        print(f"(BEFORE) unique of y_val: {np.unique(y_val)}")
        # y_train = rp.precipitationvalues_to_binary_encoding(y_train)
        # y_val = rp.precipitationvalues_to_binary_encoding(y_val)
        # print(f"(AFTER) min/max of y_train: {min(y_train)}/{max(y_train)}")
        # print(f"(AFTER) min/max of y_val: {min(y_val)}/{max(y_val)}")
        # print(f"(AFTER) unique of y_train: {np.unique(y_train)}")
        # print(f"(AFTER) unique of y_val: {np.unique(y_val)}")
        
        print(f"- Shapes of (train/val) arrays: {y_train.shape}/{y_val.shape}")
    elif prediction_task_id == rp.PredictionTask.REGRESSION:
        print("- Prediction task: regression.")
        loss = nn.MSELoss()
        global y_mean_value
        y_mean_value = np.mean(y_train)
        print(y_mean_value)
        model = RegressionNet(in_channels=NUM_FEATURES, y_mean_value=y_mean_value)

    print(model)

    print(f" - Setting up optimizer.")
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    # optimizer = torch.optim.SGD(model.parameters(), lr=1e-5, momentum=0.9)

    print(f" - Creating data loaders.")
    train_loader, val_loader = create_train_and_val_loaders(
        X_train, y_train, X_val, y_val, batch_size=BATCH_SIZE, train_weights=train_weights, val_weights=val_weights)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f" - Moving data and parameters to {device}.")
    train_loader = DeviceDataLoader(train_loader, device)
    val_loader = DeviceDataLoader(val_loader, device)
    to_device(model, device)

    print(f" - Fitting model...", end = " ")
    train_loss, val_loss = model.fit(n_epochs=N_EPOCHS,
                               optimizer=optimizer,
                               train_loader=train_loader,
                               val_loader=val_loader,
                               patience=PATIENCE,
                               criterion=loss,
                               pipeline_id=pipeline_id)
    print("Done!")

    gen_learning_curve(train_loss, val_loss, pipeline_id)

    return model


def main(argv):
    help_message = "Usage: {0} -p <pipeline_id>".format(argv[0])

    try:
        opts, args = getopt.getopt(
            argv[1:], "ht:p:r", ["help", "task=", "pipeline_id=", "reg"])
    except:
        print(help_message)
        sys.exit(2)

    # ordinal_classification = True

    prediction_task_id = None

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_message)  # print the help message
            sys.exit(2)
        elif opt in ("-t", "--task"):
            prediction_task_id_str = arg
            if prediction_task_id_str == "ORDINAL_CLASSIFICATION":
                prediction_task_id = rp.PredictionTask.ORDINAL_CLASSIFICATION
            elif prediction_task_id_str == "BINARY_CLASSIFICATION":
                prediction_task_id = rp.PredictionTask.BINARY_CLASSIFICATION
        elif opt in ("-p", "--pipeline_id"):
            pipeline_id = arg

    if prediction_task_id is None:
        prediction_task_id = rp.PredictionTask.REGRESSION

    start_time = time.time()

    seed_everything()

    #
    # Load numpy arrays (stored in a pickle file) from disk
    filename = globals.DATASETS_DIR + pipeline_id + ".pickle"
    print(f"Loading train/val/test datasets from {filename}.")
    file = open(filename, 'rb')
    (X_train, y_train, X_val, y_val, X_test, y_test) = pickle.load(file)
    print(f"Shapes of train/val/test data matrices: {X_train.shape}/{X_val.shape}/{X_test.shape}")
    print(f"Min values of train/val/test data matrices: {min(X_train.reshape(-1,1))}/{min(X_val.reshape(-1,1))}/{min(X_test.reshape(-1,1))}")
    print(f"Max values of train/val/test data matrices: {max(X_train.reshape(-1,1))}/{max(X_val.reshape(-1,1))}/{max(X_test.reshape(-1,1))}")

    if prediction_task_id == rp.PredictionTask.ORDINAL_CLASSIFICATION:
        pipeline_id += "_OC" 
    if prediction_task_id == rp.PredictionTask.BINARY_CLASSIFICATION:
        pipeline_id += "_BC" 
    elif prediction_task_id == rp.PredictionTask.REGRESSION:
        pipeline_id += "_Reg"

    #
    # Build model
    model = train(X_train, y_train, X_val, y_val, prediction_task_id, pipeline_id)

    # 
    # Load the best model
    model.load_state_dict(torch.load('../models/best_' + pipeline_id + '.pt'))

    y_test = rp.precipitationvalues_to_binary_encoding(y_test)

    model.print_evaluation_report(pipeline_id, X_test, y_test, hyper_params_dics_bc)

    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    main(sys.argv)
