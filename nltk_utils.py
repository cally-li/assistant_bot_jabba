
import numpy as np
import nltk
# nltk.download('punkt')
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()

#tokenize (split sentence into meaningful units/words)
def tokenize(sentence):
    return nltk.word_tokenize(sentence)


#lemmatize func (reduce common words down to a stem)
def lemmatize(word):
    # lemmatizer=WordNetLemmatizer()
    lemma=lemmatizer.lemmatize(word)
    return lemma
    
#numerization of words
def bag_of_words(tokenized_pattern, all_words):
    #lemmatize tokenized_pattern
    tokenized_pattern = [lemmatize(word) for word in tokenized_pattern]
    #initialize array with 0s with size = # of words
    bag = np.zeros(len(all_words), dtype=np.float32)
    #change index values in bag if word in all_words exists in tokenized pattern
    for index, word in enumerate(all_words):
        if word in tokenized_pattern:
            bag[index]=1
    return bag
