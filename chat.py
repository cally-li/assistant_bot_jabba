import random
import json
import torch
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize
from utils import get_weather, send_email, open_notes, show_calendar, add_calendar, google, music, maps

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# load necessary files and training data
with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

# set up model: define strucutre, define learned parameters, set to evaluation mode
model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()


# set up bot
bot_name = 'Jabba'
print("Jabba at your service!")

while True:

    sentence = input("You: ")

    exit_patterns = intents['intents'][1]['patterns']
    if sentence in exit_patterns:
        print(
            f"{bot_name}: {random.choice(intents['intents'][1]['responses'])}")
        break

    # tokenize/ create bag of words for input sentence
    sentence = tokenize(sentence)
    X = bag_of_words(sentence, all_words)  # returns np array
    # 1 row (1 sample), #columns = # tokenized items
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    # compute prediction : find label with highest probability
    output = model(X)
    # returns tuple (value, index) - value= max value of the passed in tensor, index= predicted label, reduce dimension/axis 1 (row)
    _, predicted = torch.max(output, dim=1)
    # retrieve the predicted tag
    tag = tags[predicted.item()]

    # compute probabilities
    # returns a list of probabilities  within a tuple
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]  # retrieve prob of predicted tag

    # respond based on predicted tag if prob >75%
    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                if tag == 'weather': #retrieve weather forecast
                    get_weather()
                elif tag == 'email': # send email
                    send_email()
                elif tag == 'note': #open notes app 
                    open_notes()
                elif tag == 'show_calendar': #show google cal events
                    show_calendar()
                elif tag == 'add_calendar': #add to google cal
                    add_calendar()
                elif tag == 'google': #google search
                    google()
                elif tag == 'maps': #look up location/directions on google maps
                    maps()
                elif tag == 'music': #spotify
                    music()
                else:
                    print(f"{bot_name}: {random.choice(intent['responses'])}")
    else:
        print(f"{bot_name}: Sorry, I don't understand...")
