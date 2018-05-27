import xml.etree.ElementTree as xmlTree
from pattern.vector import Document, NB, count, words
from pattern.web import plaintext
from pattern.db import csv
from collections import Counter

nb = NB()
wordStats = Counter()
opinionStats = Counter({'positive': 0, 'negative': 0, 'overall': 0})

for grade, opinion in csv('trainData.csv', separator = '\t'):
    comment = Document(opinion, type=int(grade), stopwords = True)
    nb.train(comment)

tree = xmlTree.parse("Posts.xml")
root = tree.getroot()

for row in root:
    doc = Document(plaintext(row.attrib['Body']), 
                filter = lambda w: w.strip("'").isalpha() and len(w) > 1,
                stopwords = False)
    opinion = nb.classify(doc)
    opinionStats['overall'] +=1
    if opinion > 0:
        opinionStats['positive'] += 1
    else:
        opinionStats['negative'] += 1
    wordStats += Counter(doc.words)

print wordStats.most_common(10)
print opinionStats


