import xml.etree.ElementTree as ET
import requests
#import datetime
import urllib3
#import fitz
import os
import pikepdf
# custom python code imports
import audit

# https://stackoverflow.com/questions/27981545
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def Download(drawingID):
   try:

      # ***** AUDIT PDF Start ***** #
      # ************************* #
      audit.PDFDownloadStart(str(drawingID))

      authToken = GetAuthToken()
      contextID = GetContextID(drawingID, authToken)
      url="https://qst-prodws01.lgeenergy.int/cws/ContentService.svc?wsdl"
      headers = {'content-type': 'text/xml', 'SOAPAction': 'urn:Core.service.livelink.opentext.com/DownloadContent'}
      body = u"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:api.ecm.opentext.com" xmlns:urn1="urn:Core.service.livelink.opentext.com">
                     <soapenv:Header>
                        <urn:OTAuthentication>
                           <urn:AuthenticationToken>""" + authToken + """</urn:AuthenticationToken>
                        </urn:OTAuthentication>
                     </soapenv:Header>
                     <soapenv:Body>
                        <urn1:DownloadContent>
                           <urn1:contextID>""" + str(contextID) + """</urn1:contextID>
                        </urn1:DownloadContent>
                     </soapenv:Body>
                  </soapenv:Envelope>"""
      response = requests.post(url,data=body,headers=headers,verify=False)
      response.raise_for_status()
      filePath = audit.PDFFolder + str(drawingID) + '.pdf'      
      with open(filePath, 'wb+') as out_file:
         pdfstart = 0
         for chunk in response.iter_content(1024):
            if "%PDF-" in str(chunk):
               pdfstart = 1
            if pdfstart == 1:
               out_file.write(chunk)

      sizeMB = os.stat(filePath).st_size / 1000.0
      
      # doc = fitz.open(filePath)
      # NumPages = str( doc.pageCount )
      
      pdf = pikepdf.Pdf.open(filePath)
      NumPages = len(pdf.pages)

      # ***** AUDIT PDF END ***** #
      # ************************* #
      audit.PDFDownloadEnd(str(drawingID),str(sizeMB),str(NumPages),'0','0','Success')
      
   except Exception as e:
      Message = str(e).replace("'","''''")
      print(Message)
      audit.PDFDownloadEnd(str(drawingID),'0','0','1','0','err:' + Message)









# %% Interface with Quest API to download PDFS   
def GetAuthToken():   
   url="https://qst-prodws01.lgeenergy.int/cws/Authentication.svc?wsdl"
   headers = {'content-type': 'text/xml', 'SOAPAction': 'urn:Core.service.livelink.opentext.com/AuthenticateUser'}
   body = u"""<soapenv:Envelope 
                  xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:urn="urn:Core.service.livelink.opentext.com">
               <soapenv:Header/>
               <soapenv:Body>
                  <urn:AuthenticateUser>
                     <urn:userName>APP1206</urn:userName>
                     <urn:userPassword>0V82HqfrE3810Z</urn:userPassword>
                  </urn:AuthenticateUser>
               </soapenv:Body>
            </soapenv:Envelope>"""

   response = requests.post(url,data=body,headers=headers,verify=False)
   content = str(response.content.decode("utf-8"))
   root = ET.fromstring( content )
   authToken = ""
   for elem in root.getiterator():
      if 'AuthenticateUserResult' in elem.tag:
         authToken = elem.text
   print (authToken)
   return authToken









def GetContextID(drawingID, authToken):   
   url="https://qst-prodws01.lgeenergy.int/cws/DocumentManagement.svc?wsdl"
   headers = {'content-type': 'text/xml', 'SOAPAction': 'urn:DocMan.service.livelink.opentext.com/GetVersionContentsContext'}
   body = u"""<soapenv:Envelope 
                  xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:urn="urn:api.ecm.opentext.com" 
                  xmlns:urn1="urn:DocMan.service.livelink.opentext.com">
               <soapenv:Header>
                  <urn:OTAuthentication>
                     <urn:AuthenticationToken>""" + authToken + """</urn:AuthenticationToken>
                  </urn:OTAuthentication>
               </soapenv:Header>
               <soapenv:Body>
                  <urn1:GetVersionContentsContext>
                     <urn1:ID>""" + str(drawingID) + """</urn1:ID>
                     <urn1:versionNum>0</urn1:versionNum>
                  </urn1:GetVersionContentsContext>
               </soapenv:Body>
            </soapenv:Envelope>"""

   response = requests.post(url,data=body,headers=headers,verify=False)
   content = str(response.content.decode("utf-8"))
   root = ET.fromstring( content )
   contextID = ""
   for elem in root.getiterator():
      if 'GetVersionContentsContextResult' in elem.tag:
         contextID = elem.text
   print(contextID)
   return contextID




