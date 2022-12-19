
##############    Additional dependencies required:    #########################

# pip install pillow
# pip install pdf2Image
# pip install opencv-python
# conda install -c conda-forge poppler
# conda install -c conda-forge pdfrw

#https://digi.bib.uni-mannheim.de/tesseract/
# C:\Path\to\Anaconda3\pkgs\pillow-7.0.0-py37hcc1f983_0\Lib\site-packages\PIL
# modified image size (Image.py)

############      Work Around          ################

#Download all dependencies and use pip install path/to/dependency
#add poppler-0.84.0-h1affe6b_0 library and openjp2.dll to poppler bin folder 




import glob
import os
import sys
import random
import math
import time

from PIL import Image
from pdf2image import convert_from_path#, convert_from_bytes
#from PyPDF2 import PdfFileReader
from pikepdf import Pdf

import numpy as np
import cv2

import pytesseract
import re
import audit
#from matplotlib import pyplot as plt

#import noise

start = time.time()
#print(time.ctime(start))
Image.MAX_IMAGE_PIXELS = None
MAX_PIXEL = 700000000
optimal_dpi = 0
scale = 10
# pdf to Image conversion
def pdfToImage(path,formt,density,descriptor):
    
    images = convert_from_path(path,fmt=formt,dpi=density,thread_count = 2,poppler_path = r'C:/quesTest/libPkg/poppler-0.84.0-h1affe6b_0/Library/bin')
    # saveImage(images,descriptor)
    return images

def saveImage(images,descriptor):
    
    if not os.path.exists('Image_Results'):
        os.makedirs('Image_Results') 
    imnumb = 0
    for img in images:
        path = os.path.join(os.path.join(os.getcwd(),'Image_Results'),f'Img_{descriptor}_{imnumb}.jpg')
        img.save(path)
        print(f'Img_{descriptor}_{imnumb}.jpg Saved')
        imnumb += 1

#cropping the pil image using a 4 tuple as coordinates
def cropping(pilImage,_4tuple):
     
    #_ 4tuple (x1-left, y1-upper, x2-right, y2-lower)
    region = pilImage.crop(_4tuple)
    return region

#converts a numpy array to image  
def showImageArray(numArr):
    
    im = Image.fromarray(numArr)
    im.show()


def pixelShift(arrayImage,median):
    im = Image.fromarray(arrayImage)
    thresh = math.floor(median*0.8)
    fn = lambda x : 255 if x > thresh else 0
    bw = im.convert('L').point(fn, mode='1')
    bw = bw.convert('RGB')
    imMatrix = np.array(bw)
    return imMatrix
#    imMatrix = np.array(pilImage)
#
#    for i in range(len(imMatrix)):
#        for j in range(len(imMatrix[0])):
#            gray = int((int(imMatrix[i,j,0])+int(imMatrix[i,j,1])+int(imMatrix[i,j,2]))/3)
#            if gray>=median*(0.8):#125-130
#                imMatrix[i,j] = (255,255,255)
#            else:
#                imMatrix[i,j] = (0,0,0)
#        
#    return imMatrix


# Vertical and horizontal lines extraction for better countour detection
def linesExtraction(image):
    
    img = np.copy(image)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    gray = cv2.bitwise_not(gray)
    
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
    
    horizontal = np.copy(bw)
    
    vertical = np.copy(bw)
    
    cols = horizontal.shape[1]
        
    horizontal_size = cols // 30
    
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    
    horizontal = cv2.erode(horizontal, horizontalStructure)
    
    horizontal = cv2.dilate(horizontal, horizontalStructure)
    
    rows = vertical.shape[0]
    
    verticalsize = rows // 30
    
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    
    vertical = cv2.erode(vertical, verticalStructure)
        
    vertical = cv2.dilate(vertical, verticalStructure)
    
    vertical = cv2.bitwise_not(vertical)
    
    horizontal = cv2.bitwise_not(horizontal)
    
    gray = cv2.bitwise_not(gray)  
    
    for i in range(len(vertical)):
        for j in range(len(vertical[0])):
            if vertical[i,j]== 0 or horizontal[i,j] == 0:
                image[i,j] = (255,255,255)
    return image
    
    
    #image pre-perocessing
def imageProcessing(image, flag):
    
    # Load image, grayscale, Gaussian blur, adaptive threshold
    if flag[0]:
        image = deNoising(image, flag[1])
    #showImageArray(image)
    image =  linesExtraction(image)
    #showImageArray(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #showImageArray(gray)
    
#    blur = cv2.GaussianBlur(gray, (9,9), 0)
#    showImageArray(blur)

    edges = cv2.Canny(gray,100,200)
    #showImageArray(edges)
#    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)
#    showImageArray(thresh)
    
    # Dilate to combine adjacent contours kernel=dilation matrix
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10,10))#9
    
    dilate = cv2.dilate(edges, kernel, iterations=4)#4
    #dilate = cv2.dilate(thresh, kernel, iterations=4)#4
    
    #showImageArray(edges)
    #showImageArray(dilate)
    
    coordinates = coordinatesExtraction(dilate,image)
    
    return coordinates
    
    
#extracting rectangular coordinates   
def coordinatesExtraction(imagePr,imageUn):
    
    coordinates = []
    
    countours, hier = cv2.findContours(imagePr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    h,w,c = imageUn.shape
    resolution = h*w
    
    for el in countours:
        x,y,w,h = cv2.boundingRect(el)
        if w*h > (0.99)*resolution:
            countours = []
            countours.append(el)
    #countours = countours[0] if len(countours) == 2 else countours[1]
    

    #adding bounding boxes around detected objects
    for c in countours:
        x,y,w,h = cv2.boundingRect(c)
        area = w*h#cv2.contourArea(c)
        if area > (0.001)*resolution:
            if area > (0.5)*resolution:
                divs = 4
                for i in range(divs):
                    x1 = x
                    y1 = y + i*int(h/divs)
                    x2 = x+w
                    y2 = y + (i+1)*int(h/divs)
                    cv2.rectangle(imageUn, (x1, y1), (x2, y2), (255,0,0), 2)
                    extraction = x1, y1, x2, y2
                    coordinates.append(extraction)
            else:
                cv2.rectangle(imageUn, (x, y), (x + w, y + h), (255,0,0), 2)
                extraction = x, y, x + w, y + h
                coordinates.append(extraction)
            
    #showImageArray(imageUn)
    return coordinates
  
     
# applying segmentation to the pil image after getting coordinates from openCV methods  
def segmentation(pilListLow,pilListHigh, drwID):
    try:
        totalPages = []
        count = -1
        for imgLow, imgHigh in zip(pilListLow,pilListHigh):
            count += 1
            flag = classifyImage(imgLow)
            coordinates = imageProcessing(np.array(imgLow),flag)
            croppings = []
            for cor in coordinates:
                #print(f"processing ----------------- {cor}")
                #rescaling
                crop = cropping(imgHigh,tuple(i*scale for i in cor))
                #tuple(i*scale for i in cor)
                if flag[0]:
                    crop = postProcessing(np.array(crop),flag[1]) 
                croppings.append(crop)
            totalPages.append(croppings)
            #audit.PDFPagePNGUpdate(str(drwID),str(count),str(combinedSize(totalPages[-1])),'0','0','0','0','Success')
        return totalPages
    except Exception as e:
        message = "Image Segmentation - " + str(e).replace("'","''''")
        #audit.PDFPagePNGUpdate(str(drwID),str(count),'0','0','0','1','0',message)  

def combinedSize(lst):
    size = 0
    for el in lst:
        size += sys.getsizeof(el)
    return size/1024/1024

def deNoising(img,median):
    
    dst = cv2.fastNlMeansDenoisingColored(img,None,10,10,7,21)
#    showImageArray(dst)
    return dst#pixelShift(dst,median)

def optimalDpi(file):

#    #using PyPDF2:
#    pdf = PdfFileReader(open(file, 'rb'))
#    pageWidth = int(pdf.getPage(0).mediaBox[2]/72)
#    pageHeight = int(pdf.getPage(0).mediaBox[3]/72)
    
    #using pikepdf better performance:
    pdf = Pdf.open(file)
    pageWidth = int(pdf.pages[0].MediaBox[2]/72)
    pageHeight = int(pdf.pages[0].MediaBox[3]/72)
    optimal = min(math.floor(math.sqrt(MAX_PIXEL/(pageWidth*pageHeight))),500)
    return optimal

def classifyImage(img):

    imgArr = np.array(img)
    gray = cv2.cvtColor(imgArr, cv2.COLOR_BGR2GRAY)
    median = np.median(gray)
    #print(median)
    return (True,median) if median <= 248 else (False,median)

def postProcessing(reading,median):
    
    image = deNoising(reading,median)
    im = Image.fromarray(image) 
    return im

def ocr(bigList, drwId):
    try:
        ocrList = []
        for index, page in enumerate(bigList):
            audit.PDFPageInsert(str(drwId),str(index))
            txtDrawing = []
            for el in page:
                pytesseract.pytesseract.tesseract_cmd = r'C:/Tesseract-OCR/tesseract.exe'
                reading = pytesseract.image_to_string(el).replace("\n"," ")
                clean = re.sub(r"[^a-zA-Z0-9]+", ' ', reading)
                txtDrawing.append(clean)
            ocrList.append(txtDrawing)
            text = readyTxt(txtDrawing)
            audit.PDFPageTXTUpdate(str(drwId),str(bigList.index(page)),str(combinedSize(txtDrawing)),str(sum([len(el) for el in ocrList[-1]])),'0','0','Success')
            audit.TXTLoad(str(drwId), str(bigList.index(page)), text)
        return ocrList
    except Exception as e:
        message = "OCRExtractText - " + str(e).replace("'","''''")
        audit.PDFPageTXTUpdate(str(drwId),str(bigList.index(page)),'0','0','1','0',message)

def readyTxt(txtList):
    finalTxt = ''
    for txt in txtList:
        finalTxt += f"{txt} "
    return finalTxt[0:8000]

def segmentationProcess(drwId):
     
    file = audit.PDFFolder + str(drwId) + '.pdf'
    optimal_dpi = optimalDpi(file)
    try:
        imagesLow = pdfToImage(file , 'jpg',optimal_dpi/scale,'low')
        imagesHigh = pdfToImage(file , 'jpg',optimal_dpi,'high')
    except Exception as e:        
        message = "ExtractPages main - " + str(e).replace("'","''''")
        audit.PDFPagePNGUpdate(str(drwId),'0','0','0','0','1','0',message)
    
    results = segmentation(imagesLow, imagesHigh, drwId)
    txtFromDrw = ocr(results, drwId)
    return txtFromDrw, results


# drawing = '3262703.pdf'
# final, cps = generalProcess(drawing)

# f = cleanText(final)
# print(f'time: {time.time()-start} seconds')

# def main():
    
#     if len(sys.argv) == 2 and '*' in sys.argv[1]:
        
#         files = glob.glob(sys.argv[1])
#         random.shuffle(files)
        
#     else:
        
#         files = sys.argv[1:]
          
#     for path in files:

#         try:
            
#             imageProcessing(path)
            
#         except Exception as e:
            
#             print('%s %s' % (path, e)) 
    


# if __name__ == '__main__':
#     main()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
