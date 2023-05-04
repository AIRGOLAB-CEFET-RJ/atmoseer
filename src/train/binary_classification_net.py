import torch
import torch.nn as nn
from torch.utils.data import TensorDataset
import torch.nn.functional as F
from train.training_utils import *
from train.evaluate import *
from rainfall_classification_base import RainfallClassificationBase
from train.early_stopping import *
import rainfall_prediction as rp
import functools
import operator
import pprint

# class ResidualBlock(nn.Module):
#     def __init__(self, in_channels, out_channels, kernel_size=3, padding=1):
#         super(ResidualBlock, self).__init__()
#         self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size, padding=padding)
#         self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size, padding=padding)
#         self.relu = nn.ReLU()
        
#     def forward(self, x):
#         residual = x
#         out = self.conv1(x)
#         out = self.relu(out)
#         out = self.conv2(out)
#         out += residual
#         out = self.relu(out)
#         return out

# class BinaryClassificationNet(nn.Module):
#     def __init__(self, in_channels):
#         super(BinaryClassificationNet, self).__init__()
#         self.conv1d_1 = nn.Conv1d(
#             in_channels=in_channels, out_channels=32, kernel_size=3, padding=2)
#         self.res_block1 = ResidualBlock(32, 16)
#         self.res_block2 = ResidualBlock(16, 32)
#         self.fc = nn.Linear(32, 1)
        
#     def forward(self, x):
#         print("conv1d_1")
#         out = self.conv1d_1(x)
#         print("res_block1")
#         out = self.res_block1(x)
#         print("res_block2")
#         out = self.res_block2(out)
#         print("GAP")
#         out = out.mean(dim=-1)  # Global Average Pooling
#         print("FC")
#         out = self.fc(out)
#         return out


#     def predict(self, X):
#         print('Making predictions with binary classification model...')
#         self.eval()
#         X_as_tensor = torch.from_numpy(X.astype('float64'))
#         X_as_tensor = torch.permute(X_as_tensor, (0, 2, 1))
#         with torch.no_grad():
#             y_pred = self(X_as_tensor.float())
#             y_pred = y_pred.detach().cpu().numpy()
#         return y_pred

#     def evaluate(self, X_test, y_test):
#         print('Evaluating binary classification model...')
#         self.eval()

#         print(f"y_test:\n {y_test}")
        
#         X_test_as_tensor = torch.from_numpy(X_test.astype('float64'))
#         X_test_as_tensor = torch.permute(X_test_as_tensor, (0, 2, 1))
#         y_test_as_tensor = torch.from_numpy(y_test.astype('float64'))

#         test_ds = TensorDataset(X_test_as_tensor, y_test_as_tensor)
#         test_loader = torch.utils.data.DataLoader(
#             test_ds, batch_size=32, shuffle=False)
#         test_loader = DeviceDataLoader(test_loader, get_default_device())

#         y_pred = None
#         with torch.no_grad():
#             for xb, _ in test_loader:
#                 yb_pred = self(xb.float())
#                 yb_pred = yb_pred.detach().cpu().numpy()
#                 yb_pred = yb_pred.reshape(-1,1)
#                 if y_pred is None:
#                     y_pred = yb_pred
#                 else:
#                     y_pred = np.vstack([y_pred, yb_pred])

#         y_pred = y_pred.round().ravel()
#         y_test = y_test.ravel()
#         print(f"y_pred:\n {y_pred}")
#         print(f"y_test:\n {y_test}")

#         export_confusion_matrix_to_latex(y_test, y_pred, rp.PredictionTask.BINARY_CLASSIFICATION)

#     def fit(self, n_epochs, optimizer, train_loader, val_loader, patience, criterion, pipeline_id):
#         # to track the training loss as the model trains
#         train_losses = []
#         # to track the validation loss as the model trains
#         valid_losses = []
#         # to track the average training loss per epoch as the model trains
#         avg_train_losses = []
#         # to track the average validation loss per epoch as the model trains
#         avg_valid_losses = []

#         # initialize the early_stopping object
#         early_stopping = EarlyStopping(patience=patience, verbose=True)

#         for epoch in range(n_epochs):

#             ###################
#             # train the model #
#             ###################
#             self.train()  # prep model for training
#             for data, target in train_loader:
#                 # clear the gradients of all optimized variables
#                 optimizer.zero_grad()

#                 # forward pass: compute predicted outputs by passing inputs to the model
#                 output = self(data.float())

#                 # calculate the loss
#                 loss = criterion(output, target.float())
#                 assert not (np.isnan(loss.item()) or loss.item() >
#                             1e6), f"Loss explosion: {loss.item()}"

#                 loss.backward()

#                 # perform a single optimization step (parameter update)
#                 optimizer.step()

#                 # record training loss
#                 train_losses.append(loss.item())

#             ######################
#             # validate the model #
#             ######################
#             self.eval()  # prep model for evaluation
#             for data, target in val_loader:
#                 # forward pass: compute predicted outputs by passing inputs to the model
#                 output = self(data.float())
#                 # calculate the loss
#                 loss = criterion(output, target.float())
#                 # record validation loss
#                 valid_losses.append(loss.item())

#             # print training/validation statistics
#             # calculate average loss over an epoch
#             train_loss = np.average(train_losses)
#             valid_loss = np.average(valid_losses)
#             avg_train_losses.append(train_loss)
#             avg_valid_losses.append(valid_loss)

#             epoch_len = len(str(n_epochs))

#             print_msg = (f'[{(epoch+1):>{epoch_len}}/{n_epochs:>{epoch_len}}] ' +
#                          f'train_loss: {train_loss:.5f} ' +
#                          f'valid_loss: {valid_loss:.5f}')

#             print(print_msg)

#             # clear lists to track next epoch
#             train_losses = []
#             valid_losses = []

#             early_stopping(valid_loss, self, pipeline_id)

#             if early_stopping.early_stop:
#                 print("Early stopping activated!")
#                 break

#         return avg_train_losses, avg_valid_losses

class BinaryClassificationNet(RainfallClassificationBase):
    def __init__(self, in_channels, input_dim):

        super(BinaryClassificationNet, self).__init__()

        self.feature_extractor = nn.Sequential(
            nn.Conv1d(in_channels=in_channels, out_channels=16, kernel_size=3, padding=3),
            nn.ReLU(inplace=True),
            nn.Dropout1d(p=0.5),

            # nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=3),
            # nn.ReLU(inplace=True),
            # nn.Dropout1d(p=0.5),

            # nn.Conv1d(in_channels=64, out_channels=32, kernel_size=3, padding=3),
            # nn.ReLU(inplace=True),
            # # nn.Dropout(p=0.5),
            # nn.Conv1d(in_channels=32, out_channels=16, kernel_size=3, padding=3),
            # nn.ReLU(inplace=True)

            # nn.Dropout(p=0.5)
            # self.bn4 = nn.BatchNorm1d(64)
            # self.dropout4 = nn.Dropout(p=0.2)
        )

        # https://datascience.stackexchange.com/questions/40906/determining-size-of-fc-layer-after-conv-layer-in-pytorch
        num_features_before_fcnn = functools.reduce(operator.mul, list(self.feature_extractor(torch.rand(1, *input_dim)).shape))

        print(f"num_features_before_fcnn = {num_features_before_fcnn}")

        self.classifier = nn.Sequential(
            # nn.Linear(896, 50),
            nn.Linear(in_features=num_features_before_fcnn, out_features=50),
            nn.ReLU(inplace=True),
            nn.Linear(50, 1),
            nn.Sigmoid()
        )
        # self.fc1 = nn.Linear(num_features_before_fcnn, 50)
        # self.fc2 = nn.Linear(50, 1)
        # self.sigmoid = nn.Sigmoid()


    def forward(self, x):
        out = self.feature_extractor(x)
        # out = nn.Flatten(1, -1)(out)
        out = out.view(out.shape[0], -1)
        out = self.classifier(out)
        return out

    # def predict(self, X):
    #     print('Making predictions with binary classification model...')
    #     self.eval()
    #     X_as_tensor = torch.from_numpy(X.astype('float64'))
    #     X_as_tensor = torch.permute(X_as_tensor, (0, 2, 1))
    #     with torch.no_grad():
    #         y_pred = self(X_as_tensor.float())
    #         y_pred = y_pred.detach().cpu().numpy()

    #     y_pred = y_pred.round().ravel()
    #     assert np.all(np.logical_or(y_pred == 0, y_pred == 1))
    #     return y_pred

    def print_evaluation_report(self, pipeline_id, X_test, y_test, hyper_params_dics):
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
        y_pred = self.evaluate(X_test, y_test)
        export_confusion_matrix_to_latex(y_test, y_pred, rp.PredictionTask.BINARY_CLASSIFICATION)

        print("\\begin{verbatim}")
        print('***Classification report***')
        print(skl.classification_report(y_test, y_pred))
        print("\\end{verbatim}")


    def evaluate(self, X_test, y_test):
        print('Evaluating binary classification model...')
        self.eval()

        assert np.all(np.logical_or(y_test == 0, y_test == 1))

        X_test_as_tensor = torch.from_numpy(X_test.astype('float64'))
        X_test_as_tensor = torch.permute(X_test_as_tensor, (0, 2, 1))
        y_test_as_tensor = torch.from_numpy(y_test.astype('float64'))

        test_ds = TensorDataset(X_test_as_tensor, y_test_as_tensor)
        test_loader = torch.utils.data.DataLoader(
            test_ds, batch_size=32, shuffle=False)
        test_loader = DeviceDataLoader(test_loader, get_default_device())

        y_pred = None
        with torch.no_grad():
            for xb, _ in test_loader:
                yb_pred = self(xb.float())
                yb_pred = yb_pred.detach().cpu().numpy()
                yb_pred = yb_pred.reshape(-1,1)
                if y_pred is None:
                    y_pred = yb_pred
                else:
                    y_pred = np.vstack([y_pred, yb_pred])

        y_pred = y_pred.round().ravel()
        assert np.all(np.logical_or(y_pred == 0, y_pred == 1))
        y_test = y_test.ravel()

        return y_pred

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
            for data, target in train_loader:
                # clear the gradients of all optimized variables
                optimizer.zero_grad()

                # forward pass: compute predicted outputs by passing inputs to the model
                output = self(data.float())

                # calculate the loss
                # print(f"output.shape: {output.shape}")
                # print(f"target.shape: {target.shape}")
                loss = criterion(output, target.float())
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
            for data, target in val_loader:
                # forward pass: compute predicted outputs by passing inputs to the model
                output = self(data.float())
                # calculate the loss
                loss = criterion(output, target.float())
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
