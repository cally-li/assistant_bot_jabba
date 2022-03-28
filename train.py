import numpy as np
import json

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from nltk_utils import bag_of_words, tokenize, lemmatize
from model import NeuralNet

# PRE-PROCESSING
# load intents training file
with open('intents.json', 'r') as f:
    intents = json.load(f)

# create lists of all existing words, tags, and x-y data
all_words = []
tags = []
xy = []  #list of tuples -each tuple holds a word/list of words (each pattern) w/ their corresponding tag

# loop through each intent segment in json 
for intent in intents['intents']:
    tag = intent['tag']
    # add tag to list
    tags.append(tag)
    for pattern in intent['patterns']:
        # tokenize each word in the sentence
        w = tokenize(pattern)
        # add to our words list
        all_words.extend(w)
        # add to xy pair
        xy.append((w, tag))

# lemmatize all words (except special characters)
ignore_chars = ['?', '.', '!', "'"]
all_words = [lemmatize(w.lower()) for w in all_words if w not in ignore_chars]

# remove duplicates (by turning list into set) and sort (turns back to list)
all_words = sorted(set(all_words))
tags = sorted(set(tags))

print(len(xy), "patterns")
print(len(tags), "tags:", tags)
print(len(all_words), "unique lemmatized words:", all_words)

# create training data
X_train = []  
y_train = []

for (pattern_sentence, tag) in xy:
    # X: create a bag of words for each pattern in xy
    bag = bag_of_words(pattern_sentence, all_words) # pattern_sentence= list of words resulting from tokenizing a pattern
    X_train.append(bag)
    # y: PyTorch CrossEntropyLoss does not need on-hot encoded vector
    label = tags.index(tag)
    y_train.append(label)

# create numpy arrays
X_train = np.array(X_train)
y_train = np.array(y_train)

# Hyper-parameters 
num_epochs = 1000
batch_size = 8
learning_rate = 0.001
input_size = len(X_train[0])
hidden_size = 8
output_size = len(tags)
print(input_size, output_size)

class ChatDataset(Dataset):

    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    # access dataset x/y values by indexing the class instance
    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    # we can call len(dataset) to return the size
    def __len__(self):
        return self.n_samples

dataset = ChatDataset()
# load dataset (Dataloader fetches data and serves it up in batches)
train_loader = DataLoader(dataset=dataset,
                          batch_size=batch_size,
                          shuffle=True,
                          num_workers=0) # num_workers= #of sub-processes to use

# use GPU device if available for faster performance
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# create model and push to device
model = NeuralNet(input_size, hidden_size, output_size).to(device)

# Loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate) # paramaters() returns learnable params(weights and biases) of a torch Module

# Train the model
for epoch in range(num_epochs):
    # unpack data from dataloader
    for (words, labels) in train_loader:
        words = words.to(device)
        # labels = labels.to(dtype=torch.long).to(device)
        labels = labels.to(device)
        
        # Forward pass:compute prediction
        outputs = model(words) #pass in x inputs to model
        # if y would be one-hot, we must apply
        # labels = torch.max(labels, 1)[1]
        loss = criterion(outputs, labels) #args of CrossEntropyLoss: (tensor input, target )
        
        # Backward propagation and optimize
        optimizer.zero_grad() # zero all gradients of model parameters
        loss.backward() #compute gradients of loss function
        optimizer.step() #update weights

    #print statistics at every 100th step
    if (epoch+1) % 100 == 0:
        print (f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')  #.item() returns 1-element tensors as a python number


print(f'final loss: {loss.item():.4f}')

#save training data
data = {
    "model_state": model.state_dict(),  #save the parameters (weights and biases) of the model
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "all_words": all_words,
    "tags": tags
}

FILE = "data.pth"
torch.save(data, FILE)

print(f'training complete. file saved to {FILE}')