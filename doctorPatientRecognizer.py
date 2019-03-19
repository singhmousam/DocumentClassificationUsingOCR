
# coding: utf-8

# In[1]:


import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import re
import os


# In[2]:


folder='/home/ikscare/Documents/Projects/Mousam/textFile'
os.chdir(folder)
textFiles=os.listdir(folder)


# In[3]:


def preprocess(sent):
    sent = nltk.word_tokenize(sent)
    sent = nltk.pos_tag(sent)
    return sent


# In[4]:


def getPersonList(document):
    """Method to read each document and return a list of all possible persons in that document
    """
    personList=[]
    #for sentences in document:
    for sentence in nltk.sent_tokenize(document):
        for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sentence))):
            if hasattr(chunk, 'label'):
                if(chunk.label()=='PERSON'):
                    personList.append(' '.join(c[0] for c in chunk))
                    
    return personList


# In[5]:


def getOrganisationList(document):
    """Method to read each document and return a list of all possible organisations in that document
    """
    organistion=[]
    #for sentences in document:
    for sent in nltk.sent_tokenize(document):
        for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
            if hasattr(chunk, 'label'):
                if(chunk.label()=='ORGANIZATION'):
                    organistion.append(' '.join(c[0] for c in chunk))
    
    return organistion


# In[6]:


def getDoctors(provider):
    """Takes persons list as input and returns probable doctors' names """
    m=[]
    for person in provider:
        for sentence in document.split('\n'):
            if person in sentence:
                if re.search('(?<=Dr. )\w+\s\w+', sentence) != None:
                    m.append((re.search('(?<=Dr. )\w+\s\w+', sentence)).group(0))
                elif re.search('\w+\s\w+\W+(?=MD *)', sentence) != None:
                    m.append((re.search('\w+\s\w+\W+(?=MD *)', sentence)).group(0))
    return m


# In[7]:


def getPatients(provider):
    """Takes persons list as input and returns probable patients name"""
    m=[]
    for person in provider:
        for sentence in document.split('\n'):
            if person in sentence:
                if 'Patient' in sentence:
                    m.append(person)
    return m


# In[8]:


fileData=[]
def readDirectory(textFiles):
    for txtFile in textFiles:
        with open(txtFile,'r') as fp:
            text=fp.read()
            text = text.strip()
            fileData.append(text)
    return fileData


# In[9]:


i=1
for document in readDirectory(textFiles):
    #tagSentences=preprocess(document)
    #print(document)
    #doc=document.split('\n')
    print('\n\nDocumnet No. ',i)
    psList=getPersonList(document)
    osList=getOrganisationList(document)
    doctors=getDoctors(psList)
    patients=getPatients(psList)
    print('Probable Doctors: ',doctors)
    print('Probable patients: ',patients)
    print('Probable organisations: ',osList)
    i+=1

