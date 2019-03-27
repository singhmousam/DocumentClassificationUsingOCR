# -*- coding: utf-8 -*-
import logging
from flask import Flask, request, jsonify, redirect, url_for, render_template
import numpy as np
import pandas as pd
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
from scipy import ndimage
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
from collections import defaultdict


# 1.2 - Conversion step
#PDF TO IMAGE 
def pdfs_to_image(folder):
	"""This function will read all the pdfs in a given directory and convert them into an images per page"""
	print('Converting pdf document to images....')
	#start = time.time()
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
	end = time.time()
	print('Time Elapsed: ',end-start)
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
        im = cv2.imread(str(imPath), cv2.IMREAD_COLOR)
        # Apply preprocessing on image
        #im = imagePreprocess(img)
        # Checking rotation
        #im=rotatationCheck(im)
        # Run tesseract OCR on image
        text = pytesseract.image_to_string(im, config=config)
        #basic preprocessing of the text
        text = text.replace('\n',' ')
        text = text.replace('\t',' ')
        text = text.replace('\n+',' ')
        text = text.replace('\t+',' ')
        text = text.rstrip()
        text = text.lstrip()
        text = text.replace(' +',' ')
        text = ''.join(char for char in text if char not in exclude)
        dataFile.append(text)
    print('Total number of images read and converted: ',len(dataFile))
    end = time.time()
    print('Time Elapsed: ',end-start)
    return dataFile


# 1.2 - Model building process
# reading the document category and keyword mapper
def readMappingDoc(directory):
    docKywrdmppr=pd.read_excel(directory)
    return docKywrdmppr

# predictor algorithm
def predictor(readContent,docKywrdmppr):
    print('Applying prediction')
    # initializing category accumulator list
    catAccum=[]
    for cat in range(len(docKywrdmppr)):
        catAccum.append(0)
    # initializing prediction list and counter
    predictedDoc = []
    confidenceScore = []
    counter=1
    # performing equality check for each word in each document
    for docs in readContent:
        for x in range(len(docKywrdmppr)):
            catAccum[x]=0
        for i in range(len(docKywrdmppr)):
            #print('------------In Document %s--------------'% docKywrdmppr['Document Type'][i])
            for word in removeStopWords(docs):
                if word.casefold() in removeStopWords(docKywrdmppr['Keywords'][i].casefold()):
                    #print(word)
                    catAccum[i]=catAccum[i]+counter
        #print(catAccum)
        ind=catAccum.index(max(catAccum))
        #print(ind)
        ab = list(set(catAccum))
        ab.sort()
        try:
            confidenceScore.append((ab[-1]-ab[-2])/(ab[-1]+0.01))
        except:
            confidenceScore.append(0.00)
        #catAccum.sort()
        #confidenceScore.append((catAccum[-1]-catAccum[-2])/(catAccum[-1]+0.01))
        if ab[-1] != 0:
            predictedDoc.append(docKywrdmppr['Document Type'][ind])
        else:
            predictedDoc.append('Not Classified')
    end = time.time()
    print('Time Elapsed: ',end-start)
    return predictedDoc,confidenceScore

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

def getDoctors(provider, document):
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

def getDoctors1(provider, document):
    """Takes persons list as input and returns probable doctors' names """
    m=[]
    for person in provider:
        for sentence in document.split('\n'):
            if person in sentence:
                if re.search('(?<=Dr. )\w+\s\w+', sentence) != None:
                    m.append((re.search('(?<=Dr. )\w+\s\w+', sentence)).group(0))
                elif re.search('\w+[.\s]*\s\w+(?=\W+MD[\W\b]*)', sentence) != None:
                    m.append((re.search('\w+[.\s]*\s\w+(?=\W+MD[\W\b]*)', sentence)).group(0))
    return m

def getDoctors0(provider, document):
    """Takes persons list as input and returns probable doctors' names """
    m=[]
    for person in provider:
        for sentence in document.split('\n'):
            if person in sentence:
                if re.search('(?<=Dr. )\w+\s\w+', sentence) != None:
                    m.append((re.findall('(?<=Dr. )\w+\s\w+', sentence)))
                elif re.search('\w+[.\s]*\s\w+(?=\W+MD[\W\b]*)', sentence) != None:
                    #print('yes')
                    m.append((re.findall('\w+[.\s]*\s\w+(?=\W+MD[\W\b]*)', sentence)))
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

def getDates(document):
    return re.findall(r"\d+[/.-]\d{2}[/.-]\d+", document)


def getPatients(provider, document):
    """Takes persons list as input and returns probable patients name"""
    m=[]
    for person in provider:
        for sentence in document.split('\n'):
            if person in sentence:
                if 'Patient' in sentence:
                    m.append(person)
    return m
 
 
def findEntities(dataFile):
    """Find entities from the document entered as argument"""
    print('Finding Entities')
    entitiesFound = []
    for text in dataFile:
        text = text.replace(' +',' ')
        document = text.strip()
        psList = getPersonList(document)
        orgList = getOrganisationList(document)
        doctors = getDoctors1(psList, document)
        patients = getPatients(psList, document)
        dates = getDates(document)
        dob = getDOB(document)
        entitiesFound.append((psList,list(set(patients)), list(set(orgList)), list(set(dob)), list(set(dates)),doctors))
    end = time.time()
    print('Time Elapsed: ',end-start)
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
    end = time.time()
    print('Time Elapsed: ',end-start)
    return jsondata

# modified writing json
def writeJsonData0(images,readContent,predictions,entitiesFound,confidenceScore):
    """Writes data to a json file"""
    jsondata = defaultdict(list)
    i=0
    for i in range(len(readContent)):
        jsondata.setdefault(predictions[i], []).append({'Document Name':images[i].rsplit('/', 1)[1],'Read data':readContent[i],'Confidence Score':confidenceScore[i],
        'Entities found':{'Person List':entitiesFound[i][0],'Provider':entitiesFound[i][5],'Probable patients':entitiesFound[i][1],
        'Provider organisation':entitiesFound[i][2],'Dates':entitiesFound[i][4],'DOB':entitiesFound[i][3]}}) 
    
    with open('outputfile.json', 'w') as f:
        json.dump(jsondata, f)
    print('Data write successful')
    end = time.time()
    print('Time Elapsed: ',end-start)
    return jsondata


# API
app = Flask(__name__)
UPLOAD_FOLDER = '/home/ikscare/Documents/Projects/Mousam/FlaskAPI'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
start = time.time()

@app.route('/')
def home():
    return  "Document Manager Home"

@app.route('/runDocumentManager', methods=["GET"])
def runDocumentManager():
	# pdf path
    #file = request.args.get('input_path')
    #file = request.headers['input_path']
    #print("File: ",file)
    #if not file:
    #    return "no input text"
    #folder="/home/ikscare/Documents/Projects/Mousam/DC_using_OCR/pdfs"
    #folder = file
    #start = time.time()
    folder = UPLOAD_FOLDER
    os.mkdir(folder+'/imageFile')
    logging.info('Output image folder created')
    pdfsList=pdfs_to_image(folder) 
    images = []
    for filename in os.listdir(folder+'/imageFile'):
        img = os.path.join(folder+'/imageFile',filename)
        if img is not None:
            images.append(img)
    
    readContent = image_to_text(images)
    logging.info('Contents of the file read')
    #end = time.time()
    #print('OCR-Conversion Time Elapsed: ',end-start)
    directory='/home/ikscare/Documents/Projects/Mousam/DC_using_OCR/DocKeyword.xls'

    docMapper = readMappingDoc(directory)
    logging.info('Model building done')
    predictions, confidenceScore = predictor(readContent,docMapper)
    logging.info('Prediction on documents done')
    entitiesFound = findEntities(readContent)
    #end = time.time()
    #print('Document-Type Prediction Time Elapsed: ',end-start)
    jd = writeJsonData0(images,readContent,predictions,entitiesFound,confidenceScore)
    logging.info('File write successful')
    logging.info('Done')
    #end = time.time()
    #print('Total Time Elapsed: ',end-start)
    return jsonify(jd)
    
filenames = []
@app.route('/uploads/',methods = ['GET','POST'])
def upload_file():
    if request.method =='POST':
        uploadedFiles = request.files.getlist('file[]')
        for file in uploadedFiles :
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            filenames.append(filename)
        return redirect(url_for('confirm'))
    return """<!doctype html>
<title>Upload new File</title>
<h1>Upload new File</h1>
<form action='' method="POST" enctype="multipart/form-data">
    <p><input type='file' name='file[]' multiple=''>
    <input type='submit' value='upload'>
    </p>
</form>"""

@app.route('/confirm')
def confirm():
    return render_template('confirm.html', numOfFiles=len(filenames))

if __name__ == '__main__':
    app.run(host='0.0.0.0')