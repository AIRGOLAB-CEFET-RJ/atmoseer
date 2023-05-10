import torch
import torch.nn as nn

class LSTMNet(nn.Module):
    def __init__(self, n_neurons, input_shape):
        super(LSTMNet, self).__init__()
        self.lstm = nn.LSTM(input_size=input_shape, hidden_size=n_neurons)
        self.fc = nn.Linear(n_neurons, 1)
    
    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out)
        return out