# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 17:12:47 2019

@author: Mousam.Singh
"""
import pandas as pd
import numpy as np
import pickle

directory='C:\\Mousam Singh\\Projects\\DC using OCR\\DocumentKeywordMapping.xlsx'
docKywrdmppr=pd.read_excel(directory)
docKywrdmppr.head()

from sklearn.feature_extraction.text import CountVectorizer
count_vect = CountVectorizer()
X_train_counts = count_vect.fit_transform(docKywrdmppr.Keywords)
X_train_counts.shape
print(X_train_counts)

# TF-IDF
from sklearn.feature_extraction.text import TfidfTransformer
tfidf_transformer = TfidfTransformer()
X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
X_train_tfidf.shape
print(X_train_tfidf)
# Machine Learning
# Training Naive Bayes (NB) classifier on training data.
#response=np.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24])
from sklearn.naive_bayes import MultinomialNB
clf = MultinomialNB().fit(X_train_tfidf, docKywrdmppr['Document Type'])
#clf = MultinomialNB().fit(X_train_tfidf, response)

# saving model
filename = 'classifier.sav'
pickle.dump(clf, open(filename, 'wb'))
print('model saved successfully')
