import cv2
import sys
import pytesseract
from pdf2image import convert_from_path

if __name__ == '__main__':
	
	if pdf_file.endswith(".pdf"):
		pages = convert_from_path('pdf_file', 500)
	
		for page in pages:
		page.save('out.jpg', 'JPEG')
	
	# Read image path from command line
	imPath = "C:\\Mousam Singh\\Projects\\DC using OCR\\computer-vision-txt-input.jpg"
	# Define config parameters.
	# '-l eng'  for using the English language 
	# '--oem 1' for using LSTM OCR Engine
	config = ('-l eng --oem 1 --psm 3')
	
	# Read image from disk
	im = cv2.imread(imPath, cv2.IMREAD_COLOR)
	# Run tesseract OCR on image
	text = pytesseract.image_to_string(im, config=config)
	# Print recognized text
	print(text)