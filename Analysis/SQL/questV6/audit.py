#import datetime

#! pip install pymssql

import pymssql
import psutil
import socket
#import signal
#import sys
import os
#import re


timeout_seconds = 300
num_processes = 30
zoom = 2 # zoom level on each page

PDFFolder = 'C:/sql/QuestText/PDF/'
PNGFolder = 'C:/sql/QuestText/PNG/'
TXTFolder = 'C:/sql/QuestText/TXT/'

hostSQL = r'VMGENENG5'
userSQL = r'LGEADINT\APP1206'
pwdSQL = '0V82HqfrE3810Z'
dbSQL = 'Generation'
VMName = socket.gethostname()









def purgeDrawingFiles(drawingID):
    for parent, dirnames, filenames in os.walk('C:/sql/QuestText/'):
        for fn in filenames:
            if str(drawingID) in fn.lower():
                os.remove(os.path.join(parent, fn))


# ***** UTILITIES ***** #
# ********************* #
def executeSQLStatement(sqlStatement):
 try:
  print(sqlStatement)
  cnxn = pymssql.connect(host=hostSQL,user=userSQL,password=pwdSQL,database=dbSQL)
  cursor = cnxn.cursor()
  cursor.execute(sqlStatement)
  cnxn.commit()
 except Exception as e:
  print('Audit - SQL: ',str(e))
  print(sqlStatement)
  executeSQLStatement(sqlStatement)




# ***** SERVER ***** #
# ****************** #
def AuditSRV():
    executeSQLStatement("""
      INSERT INTO quest.AuditSRV( datestamp, CPU, RAM, VMName ) 
      VALUES( GETDATE(), '""" + str(psutil.cpu_percent()) + """' , '""" + str(psutil.virtual_memory().percent) + """', '""" + VMName + """' )
      """)    



# ***** LOG ***** #
# *************** #
def AuditLog(process, message):
    executeSQLStatement("""
      INSERT INTO quest.AuditLog( datestamp, process, message ) 
      VALUES( GETDATE(), '""" + process + """' , '""" + str(message).replace("'","''''") + """' )
      """)





# ***** BATCH ***** #
# ***************** #
def BatchStart():
    executeSQLStatement("""
      INSERT INTO quest.AuditLog( Datestamp, Process, Message ) 
      VALUES( GETDATE(), 'Audit', 'Batch Start' )
      """)     

def BatchEnd():
    executeSQLStatement("""
      INSERT INTO quest.AuditLog( Datestamp, Process, Message ) 
      VALUES( GETDATE(), 'Audit', 'Batch End' )
      """)



# ***** PDF ***** #
# *************** #
def RerunEmptyStringErrors():
    sql = "select DrawingID from quest.Drawings where DrawingTextAll = 'b' and VMName = '" + VMName + "' order by DrawingID"

    drawings = []
    cnxn = pymssql.connect(host=hostSQL,user=userSQL,password=pwdSQL,database=dbSQL)
    cursor = cnxn.cursor()
    cursor.execute(sql)
    for row in cursor:
        drawings.append(int(row[0]))
    cnxn.commit()
    return drawings
    
def RerunTesseractErrors():
    sql = "select DrawingID from quest.Drawings where PDFSuccess is not null and (PNGSuccess is null or TXTSuccess is null) and DrawingID not in (3129085,5418828) and VMName = '" + VMName + "' order by DrawingID"

    drawings = []
    cnxn = pymssql.connect(host=hostSQL,user=userSQL,password=pwdSQL,database=dbSQL)
    cursor = cnxn.cursor()
    cursor.execute(sql)
    for row in cursor:
        drawings.append(int(row[0]))
    cnxn.commit()
    return drawings
    
def RerunErrorOnePDFDrawings():
    sql = "select d.DrawingID from quest.Drawings d inner join quest.PDFPages p on d.DrawingID = p.DrawingID where TXTMessage like '%1%' and d.VMName = '" + VMName + "'"

    drawings = []
    cnxn = pymssql.connect(host=hostSQL,user=userSQL,password=pwdSQL,database=dbSQL)
    cursor = cnxn.cursor()
    cursor.execute(sql)
    for row in cursor:
        drawings.append(int(row[0]))
    cnxn.commit()
    return drawings 
    
def QueuePDFDrawings():
    sql = "select DrawingID from quest.Drawings where VMName = '" + VMName + "' and PDFSuccess is null"

    drawings = []
    cnxn = pymssql.connect(host=hostSQL,user=userSQL,password=pwdSQL,database=dbSQL)
    cursor = cnxn.cursor()
    cursor.execute(sql)
    for row in cursor:
        drawings.append(int(row[0]))
    cnxn.commit()
    return drawings 

def QueueNewAndChangedPDFDrawings():
    sql = "select DrawingID from quest.Drawings where PDFSuccess is null"

    drawings = []
    cnxn = pymssql.connect(host=hostSQL,user=userSQL,password=pwdSQL,database=dbSQL)
    cursor = cnxn.cursor()
    cursor.execute(sql)
    for row in cursor:
        drawings.append(int(row[0]))
    cnxn.commit()
    return drawings
    
def QueueNotRanPDFDrawings():
    sql = "select distinct d.DrawingID FROM [Generation].[quest].[PDFFiles] p right join Generation.quest.Drawings d on p.DrawingID = d.DrawingID where d.VMName = '" + VMName + "' and message is null"

    drawings = []
    cnxn = pymssql.connect(host=hostSQL,user=userSQL,password=pwdSQL,database=dbSQL)
    cursor = cnxn.cursor()
    cursor.execute(sql)
    for row in cursor:
        drawings.append(int(row[0]))
    cnxn.commit()
    return drawings    
    
def QueuePDFDrawingsOLD():
    sql = "select DrawingID FROM quest.Drawings dwg where vmname = '" + VMName + "'"

    drawings = []
    cnxn = pymssql.connect(host=hostSQL,user=userSQL,password=pwdSQL,database=dbSQL)
    cursor = cnxn.cursor()
    cursor.execute(sql)
    for row in cursor:
        drawings.append(int(row[0]))
    cnxn.commit()
    return drawings    

def PDFDownloadStart(DrawingID):   
    sql = "exec [quest].[PDFDownloadStart] '" + VMName + "', " + str(DrawingID)
    #sql = "exec [quest].[PDFDownloadStart_New] '" + VMName + "', " + str(DrawingID)
    executeSQLStatement(sql)


def PDFDownloadEnd(DrawingID,SizeMB,NumPages,ErrorOut,TimeOut,Message):   
    sql = "exec [quest].[PDFDownloadEnd] '" + \
      VMName + "', " + \
      str(DrawingID) + "," + \
      str(SizeMB) + "," + \
      str(NumPages) + "," + \
      str(ErrorOut) + "," + \
      str(TimeOut) + ",'" + \
      str(Message) + "'"
    executeSQLStatement(sql)


# ***** PNG ***** #
# *************** #
def PDFPageInsert(DrawingID,PageNumber):
    sql = "exec [quest].[PDFPageInsert] '" + \
      VMName + "', " + \
      str(DrawingID) + "," + \
      str(PageNumber)
    executeSQLStatement(sql)


def PDFPagePNGUpdate(DrawingID,PageNumber,PNGSizeMB,PNGWidth,PNGHeight,ErrorOut,TimeOut,Message):
    sql = "exec [quest].[PDFPagePNGUpdate] '" + \
      VMName + "', " + \
      str(DrawingID) + "," + \
      str(PageNumber) + "," + \
      str(PNGSizeMB) + "," + \
      str(PNGWidth) + "," + \
      str(PNGHeight) + "," + \
      str(ErrorOut) + "," + \
      str(TimeOut) + ",'" + \
      str(Message) + "'"
    executeSQLStatement(sql)


def PDFPageTXTUpdate(DrawingID,PageNumber,TXTSizeMB,TXTLength,ErrorOut,TimeOut,Message):
    sql = "exec [quest].[PDFPageTXTUpdate] '" + \
      VMName + "', " + \
      str(DrawingID) + "," + \
      str(PageNumber) + "," + \
      str(TXTSizeMB) + "," + \
      str(TXTLength) + "," + \
      str(ErrorOut) + "," + \
      str(TimeOut) + ",'" + \
      str(Message) + "'"
    executeSQLStatement(sql)


def TXTLoad(drawingID, pageNumber, text):
    #executeSQLStatement("""
    #  INSERT INTO [quest].[TextFiles] VALUES (
    #  Getdate() ,
    #  '""" + drawingID + """',
    #  '""" + pageNumber + """',
    #  '""" + str(text) + """'
    #  )""")
    sql = "exec [quest].[PDFTXTLoad] '" + \
      VMName + "', " + \
      str(drawingID) + "," + \
      str(pageNumber) + ",'" + \
      str(text) + "'"
    executeSQLStatement(sql)

