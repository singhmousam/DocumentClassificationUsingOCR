"""Pass two arguments, input directory which contains pdfs and output directory where you want to save the output
Example:  python ocr.py /home/ikscare/Documents/Projects/Mousam/DC_using_OCR/pdfs /home/ikscare/Documents/Projects/Mousam"""

import cv2
import sys
import pandas as pd
import numpy as np
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
import pytesseract
from pdf2image import convert_from_path


#PDF TO IMAGE METHOD
def pdfs_to_image(folder):
	"""This function will read all the pdfs in a given directory and convert them into an images per page"""
	print('Converting pdf document to images....')
	directoryList = os.listdir(folder)
    
	for pdfFile in directoryList:
		print(pdfFile)
		if pdfFile.endswith(".pdf"): # checking for file with .pdf extension
			os.chdir(folder) 
			pages = convert_from_path(pdfFile)
			os.chdir(targetFolder+'/imageFile')
			for page in pages:
				rep=pdfFile[-3:]
				name=pdfFile.replace(rep,'txt')
				page.save("%s-page%d.tiff" %(name,pages.index(page)), 'TIFF')
	print('pdf to image conversion done')
	return directoryList

#Function to convert images to text
def images_to_text(testImg):
    print('Reading images form the directory..........')
    dataFile={} #dictonary for storing text extracted from images
    for filename in os.listdir(testImg):
        os.chdir(testImg)
        # Define config parameters.
        # '-l eng'  for using the English language 
        # '--oem 1' for using LSTM OCR Engine
        config = ('-l eng --oem 1 --psm 3')
        # Read image from disk
        im = cv2.imread(str(filename), cv2.IMREAD_COLOR)
        # Run tesseract OCR on image
        text = pytesseract.image_to_string(im, config=config)
        #performing basic preprocessing of the text
        text = text.replace('\t',' ')
        text= text.rstrip()
        text= text.lstrip()
        text = text.replace(' +',' ')
        text = text.replace('\n+','\n')
        text = text.replace('\n+ +',' ')

        os.chdir(targetFolder+'/textFile')
        #changing extension of file to .txt
        rep=filename[-3:]
        name=filename.replace(rep,'txt') 
        #writing data to file
        with open(name, 'w') as writeFile:
            writeFile.write("%s\n" % text)
        text = text.replace('\n',' ')
        dataFile[filename]=text # adding text to dictionary with file name as key
    print('Writing data to file completed successfully')    
    return dataFile

#main working 

folder="/home/ikscare/Documents/Projects/Mousam/DC_using_OCR/pdfs"
folder=sys.argv[1]
#targetFolder="/home/ikscare/Documents/Projects/Mousam/DC_using_OCR/imagesDir"
targetFolder=sys.argv[2]
os.mkdir(targetFolder+'/imageFile')
os.mkdir(targetFolder+'/textFile')
imgTxt="/home/ikscare/Documents/Projects/Mousam/DC_using_OCR/imageTxt"
	
pdfsList=pdfs_to_image(folder)
readContent=images_to_text(targetFolder+'/imageFile')

print("Conversion Done")
print('Number of pdfs read: ',len(pdfsList))
print('Total number of pages read and converted: ',len(readContent))