import logging
from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import csv
from flasgger import Swagger
import cv2
import sys
import os
import re
import pytesseract
import string
import nltk
import json
import time
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from scipy import ndimage
from pdf2image import convert_from_path
from collections import defaultdict
from nltk.tag import StanfordNERTagger


# 1.2 - Conversion step
#PDF TO IMAGE 
def pdfs_to_image(folder):
	"""This function will read all the pdfs in a given directory and convert them into an images per page"""
	print('Converting pdf document to images....')
	directoryList = os.listdir(folder)
    
	for pdfFile in directoryList:
		print(pdfFile)
		if pdfFile.endswith(".pdf"): # checking for file with .pdf extension
			os.chdir(folder) 
			pages = convert_from_path(pdfFile)
			os.chdir(folder+'/imageFile')
			for page in pages:
				rep=pdfFile[-3:]
				name=pdfFile.replace(rep,'txt')
				page.save("%s-page%d.tiff" %(name,pages.index(page)), 'TIFF')
	print('Pdf to Image conversion completed')
	print('Number of pdfs read: ',len(directoryList))
	return directoryList


# Preprocess method
def imagePreprocess(img):
    # Rescale the image, if needed.
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    # Convert to gray
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply dilation and erosion to remove some noise
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    # Apply threshold to get image with only black and white
    img = cv2.adaptiveThreshold(cv2.medianBlur(img, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    return img

# Image Rotation check
def rotatationCheck(image):
    angle = int(re.search('(?<=Rotate: )\d+', pytesseract.image_to_osd(image)).group(0))
    if angle == 0:
        return image
    rotationAngle=360-int(re.search('(?<=Rotate: )\d+', pytesseract.image_to_osd(image)).group(0))
    (h, w) = image.shape[:2]
    center = (w / 2, h / 2)
    scale = 1.0
    # Perform the rotation
    M = cv2.getRotationMatrix2D(center, rotationAngle, scale)
    rotated = cv2.warpAffine(image, M, (w, h))
    return rotated

# IMAGE TO TEXT METHOD
def image_to_text(directoryList):
    print("Reading images.......!!!!")
    dataFile=[]
    exclude=set(string.punctuation)
    for imPath in directoryList: 
        print(imPath)
        # Define config parameters.
        # '-l eng'  for using the English language 
        # '--oem 1' for using LSTM OCR Engine
        config = ('-l eng --oem 1 --psm 3')
    
        # Read image from disk
        img = cv2.imread(str(imPath), cv2.IMREAD_COLOR)
        # Apply preprocessing on image
        #im = imagePreprocess(img)
        # Checking rotation
        im=rotatationCheck(img)
        # Run tesseract OCR on image
        text = pytesseract.image_to_string(im, config=config)
        #basic preprocessing of the text
        text = text.replace('\n',' ')
        text = text.replace('\t',' ')
        text = text.replace('\n+',' ')
        text = text.replace('\t+',' ')
        text= text.rstrip()
        text= text.lstrip()
        text = text.replace(' +',' ')
        text= ''.join(char for char in text if char not in exclude)
        dataFile.append(text)
    print('Total number of images read and converted: ',len(dataFile))
    return dataFile


# 1.2 - Model building process
# reading the document category and keyword mapper
def readMappingDoc(directory):
    docKywrdmppr=pd.read_excel(directory)
    return docKywrdmppr

# predictor algorithm
def predictor(readContent,docKywrdmppr):
    # initializing category accumulator list
    catAccum=[]
    for cat in range(len(docKywrdmppr)):
        catAccum.append(0)
    # initializing prediction list and counter
    predictedDoc=[]
    counter=1
    # performing equality check for each word in each document
    for docs in readContent:
        for x in range(len(docKywrdmppr)):
            catAccum[x]=0
        for i in range(len(docKywrdmppr)):
            print('------------In Document %s--------------'% docKywrdmppr['Document Type'][i])
            for word in removeStopWords(docs):
                if word.casefold() in removeStopWords(docKywrdmppr['Keywords'][i].casefold()):
                    print(word)
                    catAccum[i]=catAccum[i]+counter
        print(catAccum)
        ind=catAccum.index(max(catAccum))
        print(ind)
        predictedDoc.append(docKywrdmppr['Document Type'][ind])
    return predictedDoc

# method for removing stop words
def removeStopWords(docs):
    stop_words = set(stopwords.words('english')) 
    #for docs in readContent:
    word_tokens = word_tokenize(docs)
    filtered_sentence = [w for w in word_tokens if not w in stop_words]
    filtered_sentence = [] 
    for w in word_tokens: 
        if w not in stop_words:
            filtered_sentence.append(w)
    filt_set=set(filtered_sentence)
    filtered_sentence=list(filt_set)
    return filtered_sentence

	
# 1.3 - Entity recognition
def preprocess(sent):
    sent = nltk.word_tokenize(sent)
    sent = nltk.pos_tag(sent)
    return sent

def getPersonListSTANFORD(document):
    """Method to read each document and return a list of all possible persons in that document
    """
    personList = []
    # tag named entities
    ner_tagged_sentences = [sn.tag(sent.split()) for sent in document]
    # combining same entities together
    overall_Entities = []
    tags_Entities = []
    from itertools import groupby
    for sentence in ner_tagged_sentences:
        for tag, chunk in groupby(sentence, lambda x:x[1]):
            if tag != "O":
                tags_Entities.append(tag)
                overall_Entities.append(" ".join(w for w, t in chunk))
    # zipping tag and entities
    zipped_data = list(set(zip(tags_Entities,overall_Entities)))
    # fiding PERSON tag from all the tags
    for d in zipped_data:
        if d[0] == 'PERSON':
            personList.append(d[1])

    return personList

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

def getDoctors0(provider, document):
    """Takes persons list as input and returns probable doctors' names """
    m=[]
    for person in provider:
        for sentence in document.split('\n'):
            if person in sentence:
                if re.search('(?<=Dr. )\w+\s\w+', sentence) != None:
                    m.append(re.findall('(?<=Dr. )\w+\s\w+', sentence))
                elif re.search('\w+[.\s]*\s\w+(?=\W+MD[\W\b]*)', sentence) != None:
                    #print('yes')
                    m.append(re.findall('\w+[.\s]*\s\w+(?=\W+MD[\W\b]*)', sentence))
    return m

def getDOB(document):
    dateList=[]
    date_strings = re.findall(r"\d+[/.-]\d{2}[/.-]\d+", document)
    for date in date_strings:
        for sentence in document.split('\n'):
            if date in sentence:
                if 'DOB' in sentence:
                    dateList.append(date)
    return dateList


def getPatients(provider, document):
    """Takes persons list as input and returns probable patients name"""
    m=[]
    for person in provider:
        for sentence in document.split('\n'):
            if person in sentence:
                if 'Name' in sentence:
                    m.append(person)
    return m
 
 
def findEntities(dataFile):
    """Find entities from the document entered as argument"""
    entitiesFound = []
    for text in dataFile:
        text = text.replace(' +',' ')
        document = text.strip()
        psList = getPersonList(document)
        orgList = getOrganisationList(document)
        doctors = getDoctors0(psList, document)
        patients = getPatients(psList, document)
        dob = getDOB(document)
        entitiesFound.append((doctors, list(set(patients)), list(set(orgList)), list(set(dob))))
    return entitiesFound
	
# write data in json file
def writeJsonData(images,readContent,predictions,entitiesFound):
    """Writes data to a json file"""
    jsondata = {}
    i=0
    for i in range(len(readContent)):
        jsondata[images[i]] = {'data':readContent[i], 'Precdicted Type':predictions[i], 
        'Entities found':{'doctor':entitiesFound[i][0],'patients':entitiesFound[i][1],
        'provider organisation':entitiesFound[i][2],'DOB':entitiesFound[i][3]}}
    
    with open('outputfile.json', 'w') as f:
        json.dump(jsondata, f)
    print('Data write successful')
    return jsondata

# modified writing json
def writeJsonData0(images,readContent,predictions,entitiesFound):
    """Writes data to a json file"""
    jsondata = defaultdict(list)
    i=0
    for i in range(len(readContent)):
        jsondata[predictions[i]].append({'Document Name':images[i].rsplit('/', 1)[1],'data':readContent[i], 
        'Entities found':{'doctor':entitiesFound[i][0],'patients':entitiesFound[i][1],
        'provider organisation':entitiesFound[i][2],'DOB':entitiesFound[i][3]}})
    
    with open('outputfile.json', 'w') as f:
        json.dump(jsondata, f)
    print('Data write successful')
    return jsondata


# API
app = Flask(__name__)
UPLOAD_FOLDER = '/home/ikscare/Documents/Projects/Mousam/FlaskAPI'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return  "HOME PAGE LOADED"

@app.route('/runDocumentManager', methods=["GET"])
def runDocumentManager():
    # Initialize stanford NER tagger
    sn = StanfordNERTagger("/home/ikscare/Documents/Projects/Mousam/stanford-ner-2014-08-27/classifiers/english.all.3class.distsim.crf.ser.gz",
                       path_to_jar="/home/ikscare/Documents/Projects/Mousam/stanford-ner-2014-08-27/stanford-ner.jar")

	# pdf path
    file = request.args.get('input_path')
    start = time.time()
    #file = request.headers['input_path']
    print("File: ",file)
    if not file:
        return "no input text"
    #folder="/home/ikscare/Documents/Projects/Mousam/DC_using_OCR/pdfs"
    folder = file
    os.mkdir(folder+'/imageFile')
    logging.info('Output image folder created')
    pdfsList=pdfs_to_image(folder)
    end = time.time()
    images = []
    for filename in os.listdir(folder+'/imageFile'):
        img = os.path.join(folder+'/imageFile',filename)
        if img is not None:
            images.append(img)
    
    readContent = image_to_text(images)
    print('OCR-Conversion Time Elapsed: ',end-start) 
    logging.info('Contents of the file read')

    directory='/home/ikscare/Documents/Projects/Mousam/DC_using_OCR/DocKeyword.xls'

    docMapper = readMappingDoc(directory)
    logging.info('Model building done')
    predictions = predictor(readContent,docMapper)
    logging.info('Prediction on documents done')
    entitiesFound = findEntities(readContent)
    end = time.time()
    print('Document-Type Prediction Time Elapsed: ',end-start)
    jd = writeJsonData0(images,readContent,predictions,entitiesFound)
    end = time.time()
    logging.info('File write successful')
    logging.info('Done')
    print('Total Time Elapsed: ',end-start)
    return jsonify(jd)
    

@app.route('/uploads/',methods = ['GET','POST'])
def upload_file():
    if request.method =='POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            return hello()
    return """<!doctype html>
<title>Upload new File</title>
<h1>Upload new File</h1>
<form action='' method="POST" enctype="multipart/form-data">
    <p><input type='file' name='file[]' multiple=''>
    <input type='submit' value='upload'>
    </p>

</form>"""


if __name__ == '__main__':
    app.run(host='0.0.0.0')