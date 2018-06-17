from functools import reduce

import nltk
from nltk.tokenize import word_tokenize


class Tagger(object):
    def __init__(self, trainData = []):
        self._trainData = trainData
        self._classifier = None
        self.trainKeywords = []
        if len(self._trainData) > 0:
            self.constructTrainingSet()
            self._classifier = nltk.NaiveBayesClassifier.train(self.trainingSet)
    
    def tag(self, text):
        textFeatures = {word.lower(): (word in word_tokenize(text.lower())) for word in self.trainKeywords}
        result = self._classifier.prob_classify(textFeatures)
        probabilityRes = [(tag, result.prob(tag)) for tag in result.samples()]
        avg = sum([sample[1] for sample in probabilityRes]) / len(probabilityRes)
        return [results[0] for results in probabilityRes if results[1] > 2*avg]
        
    def constructTrainingSet(self):
        trainList = []
        for trainSample in self._trainData:
            for tag in trainSample[1]:
                trainList.append((trainSample[0], tag))
            for tag in trainSample[0].split(' '):
                trainList.append((tag, tag))
        self.trainKeywords = set(word.lower() for trainSample in trainList for word in word_tokenize(trainSample[0]))
        self.trainingSet = [({word: (word in word_tokenize(trainSample[0])) for word in self.trainKeywords}, trainSample[1]) for trainSample in trainList]
        

multiple_train_data = [('.net c# wpf uwp asp.net xamarin', ['.net', 'c#']),
                       ('autofac windsor simpleinjector', ['ioc', 'container']),
                       ('postgre sqlserver mongo cassandra oracle mysql', ['database']),
                       ('aws azure', ['cloud']),
                       ('c++ cmake boost opencv iostream visual-c++ memory-leak', ['c++'])
                       ]



with open("input", "r") as f:
    content = f.read().replace('\n', '');
    print(content.lower())
    tagger = Tagger(multiple_train_data)
    print(tagger.tag(content))
