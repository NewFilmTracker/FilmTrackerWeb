from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn
from nltk.corpus import sentiwordnet as swn
from nltk import sent_tokenize, word_tokenize, pos_tag
from nltk.sentiment.util import mark_negation
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.base import TransformerMixin
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.linear_model import LogisticRegression
from sklearn.externals import joblib
import re
import nltk
from sklearn.model_selection import train_test_split
import classifier_en
import dataProcessor

threshold = 0.6

def predictTweets(tweets, clf) :
    return clf.predict(tweets)

def stemming_tokenizer(sentence):
    stemmer = PorterStemmer()
    sentence = word_tokenize(sentence)
    stop_words = set(stopwords.words('english'))
    newsentence = []
    for word in sentence :
        if word not in stop_words :
            if len(word) >=3:
                newsentence.append(word)

    newsentence = mark_negation(newsentence)
    return newsentence


def predictProbaTweets(tweets, clf) :
    if "predict_proba" in dir(clf) :
        return clf.predict_proba(tweets)
    else:
        raise Exception('Error use Logistic Regression classifier')

def labelTweets(tweets, proba) :
    newtweetsPos = []
    countPos = 0
    newtweetsNeg = []
    countNeg = 0
    newtweetsUnknown = []
    countUnknown = 0
    for i in range(0, len(tweets)):
        newtweets = tweets[i]
        label = 0
        if proba[i][0] >= threshold:
            label = 1
        else :
            if proba[i][1] >= threshold:
                label = 2
        if label == 0 :
            newtweetsUnknown.append(newtweets)
            countUnknown += 1
        elif label == 1 :
            newtweetsPos.append(newtweets)
            countPos += 1
        else :
            newtweetsNeg.append(newtweets)
            countNeg += 1

    return {
        'text' : {
            'pos': newtweetsPos, 'neg':newtweetsNeg, 'unknown':newtweetsUnknown
        },
        'count' : {
            'pos':countPos, 'neg':countNeg, 'unknown':countUnknown
        }
    }




def analyzeTweet(id, query):
    clf = joblib.load('model/clf-LogisticRegression-100.pkl')

    tweets_ori = dataProcessor.requestDataFromAPI('en', query, 100)
    tweets = tweets_ori['tweet']
    for i in range(0, len(tweets)):
        tweets[i] = cleanTotalTweet(tweets[i], query)

    proba = [""]*len(tweets)
    proba = predictProbaTweets(tweets, clf)

    dataTweets = getTweetFromMaxProb(tweets_ori, proba)
    message = {}
    message['id'] = id
    message['query'] = query
    message['hasil'] = dataTweets

    print(message)

    # for i in range(0, len(tweets)) :
    #     print(tweets[i]+"\t"+str(label[i])+" "+str(proba[i]))

if __name__ == '__main__':
   analyzeTweet(1, "#jigsaw")
