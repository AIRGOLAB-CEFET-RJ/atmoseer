"""
    https://stats.stackexchange.com/questions/209290/deep-learning-for-ordinal-classification

    https://towardsdatascience.com/simple-trick-to-train-an-ordinal-regression-with-any-classifier-6911183d2a3c

    https://towardsdatascience.com/how-to-perform-ordinal-regression-classification-in-pytorch-361a2a095a99

    https://arxiv.org/pdf/0704.1028.pdf

    https://datascience.stackexchange.com/questions/44354/ordinal-classification-with-xgboost

    https://towardsdatascience.com/building-rnn-lstm-and-gru-for-time-series-using-pytorch-a46e5b094e7b

    https://neptune.ai/blog/how-to-deal-with-imbalanced-classification-and-regression-data

    https://colab.research.google.com/github/YyzHarry/imbalanced-regression/blob/master/tutorial/tutorial.ipynb#scrollTo=tSrzhog1gxyY
"""

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset
import torch.nn.functional as F
from train.training_utils import *
from train.evaluate import *
from rainfall import ordinal_encoding_to_level
from train.early_stopping import *
import rainfall as rp
import pprint
import globals as globals

class OrdinalClassificationNet(nn.Module):
    def __init__(self, in_channels, num_classes):
        super(OrdinalClassificationNet, self).__init__()
        self.conv1d_1 = nn.Conv1d(
            in_channels=in_channels, out_channels=32, kernel_size=3, padding=2)
        self.conv1d_2 = nn.Conv1d(
            in_channels=32, out_channels=32, kernel_size=3, padding=2)
        self.conv1d_3 = nn.Conv1d(
            in_channels=32, out_channels=32, kernel_size=3, padding=2)
        self.conv1d_4 = nn.Conv1d(
            in_channels=32, out_channels=64, kernel_size=3, padding=2)

        # self.relu = nn.ReLU()
        self.relu = nn.GELU()

        self.sigmoid = nn.Sigmoid()

        self.fc1 = nn.Linear(896, 50)

        self.fc2 = nn.Linear(50, num_classes)

    def forward(self, x):
        x = self.conv1d_1(x)
        x = self.relu(x)

        # x = self.max_pooling1d_1(x)

        x = self.conv1d_2(x)
        x = self.relu(x)

        x = self.conv1d_3(x)
        x = self.relu(x)

        x = self.conv1d_4(x)

        x = self.relu(x)

        x = x.view(x.shape[0], -1)

        x = self.fc1(x)
        x = self.relu(x)

        x = self.fc2(x)
        x = self.sigmoid(x)

        return x

    # def prediction2label(pred: np.ndarray):
    #   """Convert ordinal predictions to class labels, e.g.

    #   [0.9, 0.1, 0.1, 0.1] -> 0
    #   [0.9, 0.9, 0.1, 0.1] -> 1
    #   [0.9, 0.9, 0.9, 0.1] -> 2
    #   etc.
    #   """
    #   return (pred > 0.5).cumprod(axis=1).sum(axis=1) - 1

    def training_step(self, batch):
        X_train, y_train = batch
        out = self(X_train)                  # Generate predictions
        loss = F.cross_entropy(out, y_train)  # Calculate loss
        return loss

    def validation_step(self, batch):
        X_train, y_train = batch
        out = self(X_train)                    # Generate predictions
        loss = F.cross_entropy(out, y_train)   # Calculate loss
        acc = accuracy(out, y_train)           # Calculate accuracy
        return {'val_loss': loss, 'val_acc': acc}

    def validation_epoch_end(self, outputs):
        batch_losses = [x['val_loss'] for x in outputs]
        epoch_loss = torch.stack(batch_losses).mean()   # Combine losses
        batch_accs = [x['val_acc'] for x in outputs]
        epoch_acc = torch.stack(batch_accs).mean()      # Combine accuracies
        return {'val_loss': epoch_loss.item(), 'val_acc': epoch_acc.item()}

    def epoch_end(self, epoch, result):
        print("Epoch [{}], val_loss: {:.4f}, val_acc: {:.4f}".format(
            epoch, result['val_loss'], result['val_acc']))

    def predict(self, X):
        print('Making predictions with ordinal classification model...')
        self.eval()

        X_as_tensor = torch.from_numpy(X.astype('float64'))
        X_as_tensor = torch.permute(X_as_tensor, (0, 2, 1))

        outputs = []
        with torch.no_grad():
            output = self(X_as_tensor.float())
            yb_pred_encoded = output.detach().cpu().numpy()
            yb_pred_decoded = ordinal_encoding_to_level(yb_pred_encoded)
            outputs.append(yb_pred_decoded.reshape(-1, 1))

        y_pred = np.vstack(outputs)

        return y_pred

    def evaluate(self, X_test, y_test):
        print('Evaluating ordinal classification model...')
        self.eval()

        test_x_tensor = torch.from_numpy(X_test.astype('float64'))
        test_x_tensor = torch.permute(test_x_tensor, (0, 2, 1))
        test_y_tensor = torch.from_numpy(y_test.astype('float64'))

        test_ds = TensorDataset(test_x_tensor, test_y_tensor)
        test_loader = torch.utils.data.DataLoader(
            test_ds, batch_size=32, shuffle=False)
        test_loader = DeviceDataLoader(test_loader, get_default_device())

        test_losses = []
        outputs = []
        with torch.no_grad():
            for xb, _ in test_loader:
                output = self(xb.float())
                yb_pred_encoded = output.detach().cpu().numpy()
                yb_pred_decoded = ordinal_encoding_to_level(yb_pred_encoded)
                outputs.append(yb_pred_decoded.reshape(-1, 1))

        y_pred = np.vstack(outputs)

        return y_pred

    def print_evaluation_report(self, pipeline_id, X_test, y_test, hyper_params_dics):
        self.load_state_dict(torch.load(globals.MODELS_DIR + '/best_' + pipeline_id + '.pt'))
        y_test = rp.value_to_level(y_test)

        print("\\begin{verbatim}")
        print(f"***Evaluation report for pipeline {pipeline_id}***")
        print("\\end{verbatim}")

        print("\\begin{verbatim}")
        print("***Hyperparameters***")
        pprint.pprint(hyper_params_dics)
        print("\\end{verbatim}")

        print("\\begin{verbatim}")
        print("***Model architecture***")
        print(self)
        print("\\end{verbatim}")

        print("\\begin{verbatim}")
        print('***Confusion matrix***')
        print("\\end{verbatim}")

        print(f"y_test.shape: {y_test.shape}")
        print(f"y_test[:50]: {y_test[:50]}")
        print(f"np.unique(y_test.shape): {np.unique(y_test)}")

        y_pred = self.evaluate(X_test, y_test)

        print(f"y_pred.shape: {y_pred.shape}")
        print(f"y_pred[:50]: {y_pred[:50]}")
        print(f"np.unique(y_pred.shape): {np.unique(y_pred)}")

        export_confusion_matrix_to_latex(
            y_test, y_pred, rp.PredictionTask.ORDINAL_CLASSIFICATION)

        print("\\begin{verbatim}")
        print('***Classification report***')
        print(skl.classification_report(y_test, y_pred))
        print("\\end{verbatim}")

    def fit(self, n_epochs, optimizer, train_loader, val_loader, patience, criterion, pipeline_id):
        # to track the training loss as the model trains
        train_losses = []
        # to track the validation loss as the model trains
        valid_losses = []
        # to track the average training loss per epoch as the model trains
        avg_train_losses = []
        # to track the average validation loss per epoch as the model trains
        avg_valid_losses = []

        # initialize the early_stopping object
        early_stopping = EarlyStopping(patience=patience, verbose=True)

        for epoch in range(n_epochs):

            ###################
            # train the model #
            ###################
            self.train()  # prep model for training
            for data, target, w in train_loader:
                # clear the gradients of all optimized variables
                optimizer.zero_grad()

                # forward pass: compute predicted outputs by passing inputs to the model
                output = self(data.float())

                # calculate the loss
                loss = criterion(output, target.float(), w)
                assert not (np.isnan(loss.item()) or loss.item() >
                            1e6), f"Loss explosion: {loss.item()}"

                loss.backward()

                # perform a single optimization step (parameter update)
                optimizer.step()

                # record training loss
                train_losses.append(loss.item())

            ######################
            # validate the model #
            ######################
            self.eval()  # prep model for evaluation
            for data, target, w in val_loader:
                # forward pass: compute predicted outputs by passing inputs to the model
                output = self(data.float())
                # calculate the loss
                loss = criterion(output, target.float(), w)
                # record validation loss
                valid_losses.append(loss.item())

            # print training/validation statistics
            # calculate average loss over an epoch
            train_loss = np.average(train_losses)
            valid_loss = np.average(valid_losses)
            avg_train_losses.append(train_loss)
            avg_valid_losses.append(valid_loss)

            epoch_len = len(str(n_epochs))

            print_msg = (f'[{(epoch+1):>{epoch_len}}/{n_epochs:>{epoch_len}}] ' +
                         f'train_loss: {train_loss:.5f} ' +
                         f'valid_loss: {valid_loss:.5f}')

            print(print_msg)

            # clear lists to track next epoch
            train_losses = []
            valid_losses = []

            early_stopping(valid_loss, self, pipeline_id)

            if early_stopping.early_stop:
                print("Early stopping activated!")
                break

        return avg_train_losses, avg_valid_losses
