import psutil, signal, time, datetime, sys, os

# timeout in seconds
tesseract_timeout = 0#1200

def checkProcess(proc, procName):
    try:
        processName = proc.name()
        processID = proc.pid
        createTime = proc.create_time()
        currentTime = time.time()
        diff = currentTime - createTime
        if procName in processName:
            if diff > tesseract_timeout:
                print(processName , ' ::: ', processID , ' ::: ', diff )
                os.kill(processID, signal.SIGINT)    
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        print("error")



try:
    for proc in psutil.process_iter():
        checkProcess(proc,"WerFault.exe") 

    for proc in psutil.process_iter():
        checkProcess(proc,"tesseract") 
except:
    print("Unexpected error:", sys.exc_info()[0])