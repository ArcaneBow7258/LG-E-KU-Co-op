#import random
#import shutil
#import sys
#import os
from multiprocessing import Process, Queue

# custom python code imports
import QuestWebService
import audit
import segmentation_Core
import time
import os
import sys
queue = Queue()
numPDF = int(sys.argv[1])

def mp_handler():

    processes = [Process(target=process_queue, args=(queue,)) for _ in range(numPDF)]

    for process in processes:
        process.start()

    for process in processes:
        process.join()

def process_queue(queue):

    while queue.qsize() > 0 :
        drawingID = queue.get()
        QuestWebService.Download(drawingID)
        
        segmentation_Core.segmentationProcess(drawingID)
        
        audit.purgeDrawingFiles(drawingID)

        print("succesfull termination")
        
if __name__ == '__main__':
    try:
        #os.chdir("C:/SQL/questV6")
        audit.BatchStart()

        #drawings = audit.QueuePDFDrawingsOLD()  #Original
        drawings = audit.QueuePDFDrawings()
        #drawings = audit.RerunEmptyStringErrors()
        
#        for id in drawings:
#            queue.put(id)    
        for i in range(numPDF):
            queue.put(drawings[i]) 
        
        #queue.put(drawings[0])


        mp_handler()

        audit.BatchEnd()
    except Exception as e:
        audit.AuditLog("main", str(e))
    sys.exit()
