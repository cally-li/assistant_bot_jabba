import torch
import torch.nn as nn


class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(NeuralNet, self).__init__() #access methods of parent class (nn.Module)
        self.l1 = nn.Linear(input_size, hidden_size)  # first layer: accepts tensor size as input, outputs tensor of hidden size
        self.l2 = nn.Linear(hidden_size, hidden_size) 
        self.l3 = nn.Linear(hidden_size, num_classes) # final layer output = # of y values
        self.relu = nn.ReLU() # activation function=rectified linear unit function
    
    def forward(self, x):
        out = self.l1(x)
        out = self.relu(out)
        out = self.l2(out)
        out = self.relu(out)
        out = self.l3(out)
        # no activation / no softmax at the end (included w/ cross entropy loss)
        return out