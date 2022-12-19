#Import Libraries
import pyspark
import pyodbc
from pyspark import SparkContext, SparkConf
import sys
from pyspark.sql.window import Window
from pyspark.sql.types import *
from pyspark.sql import functions as F
import pyspark.sql.functions as func
import numpy as np
import pandas as pd
import datetime as dt
#import seaborn as sns
import pyarrow.parquet as pq
import random
import getpass
import urllib3
urllib3.disable_warnings()
from datetime import datetime, timedelta
from pytz import timezone, all_timezones
import os.path
#Will Eventually Change to Import a Daterange but alas not available right now.
#Assuming what we will pull in will be convwerted to a Date-Time
CONFIG = {'PIWEBAPI_URL' : '',
            'SERVER' : 'corppisys01',
            'SECURITY_METHOD' : 'basic',
            'USER' : '',
            'PASSW' : '', #
            'VERIFY_SSL' : False}
sys.path.insert(1,'/u01/JupyterFolder/Test/Analysis')
from ExtractPIData import * 

#Spark set up
conf = SparkConf()
conf.setAppName("DataQualityAudit")
conf.set('spark.jars', '/u00/spark/postgresql-42.2.9.jar')
conf.set('spark.master', '')
maxcores = 5
conf.set('spark.cores.max', maxcores)
conf.set('spark.executor.memory', '64g')
conf.set('spark.driver.memory', '64g')
conf.set('spark.executor.cores', 5)
conf.set('spark.driver.maxResultSize', '64g')
    #conf.set('spark.sql.session.timeZone', 'EST')
sc = SparkContext.getOrCreate(conf=conf)
sqlContext = SQLContext(sc)
url = 'postgresql://localhost:5432/GENERATION'
propertiesTAG = {'user':'', 'password':'?', 'driver':'org.postgresql.Driver', 'numPartitions':'4', 'fetchsize':'100'}
pd.options.mode.chained_assignment = None


#Tag
TagQuery = f"(SELECT \"TAG_PI\",\"TAGID_PI\" FROM \"PI\".\"PITAG\") as a"
df_tags = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=TagQuery, properties=propertiesTAG)
tags_lst = df_tags.collect()
#tags_lst = list(pandas_tags['TAG_PI']) #Maybe change to TAGID_PI


#Time
TimeQuery = f"(SELECT \"Table\", \"StartTime\", \"EndTime\", \"LastChanged\" FROM \"PI\".\"TimeRanges\") as b"
df_time = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=TimeQuery, properties=propertiesTAG)
startTime = df_time.select(min_('StartTime')).first()[0]
endTime = df_time.select(max_('EndTime')).first()[0] - timedelta(minutes=1)
df_time.show()

#random
print("Range: ")
print(startTime)
print(endTime)
targetTag = tags_lst[random.randint(0,len(tags_lst) - 1)]['TAG_PI']
targetTime = endTime - timedelta(days = random.randint(0,(endTime-startTime).days - 1), hours=  random.randint(0, 24), minutes =  random.randint(0,60)) 
print("Targets: ")
print(targetTag)
print(targetTime)
#
#MillCreek.U2.2RH1C23.MODE
#Brown.U7.DME_AUX:W/V:
#Millcreek.U4.4TRK12AO.AUTOMANA.OP


piGood = True
piErr = ''
#Catching Errors in Pi and getting value
try:
    rawValue =  PIData(targetTag, targetTime.strftime("%Y-%m-%d %H:%M:%S") , (targetTime +  timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S") , extMethod = "WebAPI")
    piValue = rawValue['value'][0]
    print(piValue)
    try:
        piValue = piValue / 1
    except:
        if(isinstance(piValue, str)): #Ann was correct
            if(piValue.isNumeric):
               print('Theres a string! and it\'s numeric!')
               piValue = float(rawValue['value'][0]) / 1
            else:
                print('pi is weird')
                piGood = False
                piError = 'Got a string baby'
        else:
            print('pi is weird')
            piGood = False
            piError = 'Dictionary Value from pi'
except AttributeError:
    piError = 'Tag doesn\'t exist in Pi'
    print(piError)
    piGood = False
except Exception as e:
    print('Uncaught Error')
    piError = e
    piGood = False
    print(e)
        
        
#Getting all the data points
#I will one day merge all this into a single function so i don't have to repeat the "try doing tihs then except that"
interpGood = True
archiveGood = True
parquetGood = True
interpErr = ''
archiveErr = ''
parquetErr = ''
interpValue = None
archiveValue = None
interpValue = None
margins = .1
#Interp | InterpArchive | Parquet
startInterp = df_time.where(df_time['Table'] == "Interp").first()['StartTime']
startInterpArchive = df_time.where(df_time['Table'] == "InterpArchive").first()['StartTime']
endInterpArchive = df_time.where(df_time['Table'] == "InterpArchive").first()['EndTime']
endParquet = df_time.where(df_time['Table'] == "Parquet").first()['EndTime']
if(piGood):
    if( startInterpArchive <= targetTime and targetTime <= endParquet):
        print('Overlapping Time')
    #Maybe can lose a line or two using "best" method
    if( targetTime <= endParquet):
        try:
            print('Parquet')
            parquetValue = PIData(targetTag, targetTime.strftime("%Y-%m-%d %H:%M:%S") , (targetTime +  timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S") , extMethod = "parquet", datatype = 'spark').collect()[0]['value']
            print(parquetValue)
            if(abs(piValue - float(parquetValue))/piValue > margins):
                parquetGood = False
        except IndexError:
            print('index error')
            parquetErr = 'Parquet returned no value'
            parquetGood = False
        except Exception as e:
            print('parquet Error')
            parquetGood = False
            parquetErr = 'We did not check for: ' + str(e)
    if ( startInterpArchive <= targetTime and targetTime <= endInterpArchive):
        try:
            print('InterpArchive')
            archiveValue =  PIData(targetTag, targetTime.strftime("%Y-%m-%d %H:%M:%S") , (targetTime +  timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S") , extMethod = "InterpArchive", datatype = 'spark').collect()[0]['value']
            print(archiveValue)
            if(abs(piValue - float(archiveValue))/piValue > margins):
                archiveGood = False
        except IndexError:
            print('index error')
            archiveErr = 'InterpArchive returned no value'
            archiveGood = False
        except Exception as e:
            print('archive Error')
            archiveGood = False
            archiveErr = 'We did not check for: ' + str(e)
            
    if (startInterp <= targetTime):
        try:
            print('Interp')
            interpValue =  PIData(targetTag, targetTime.strftime("%Y-%m-%d %H:%M:%S") , (targetTime +  timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S") , extMethod = "interp", datatype = 'spark').collect()[0]['value']
            print(interpValue)
            if(abs(piValue - float(interpValue))/piValue > margins):
                interpValue = False
        except IndexError:
            print('index error')
            interpErr = 'Interp returned no value'
            interpGood = False
        except Exception as e:
            print('interp Error')
            interpGood = False
            interpErr = 'We did not check for: ' + str(e)
    if(not (parquetGood and archiveGood and interpGood)):
        print("OH NO SOMETHING WENT WRONG")
        with open(f'/u01/JupyterFolder/Test/Analysis/AlvinCode/DataQualityAudit{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}.txt', 'w') as f:
            f.write("Target Tag: " + targetTag)
            f.write("\nProbe Time: " + targetTime.strftime("%Y-%m-%d %H:%M:%S"))
            f.write("\nPi Value: " + str(piValue))
            interpOut = interpValue if(interpGood) else interpErr
            archiveOut = archiveValue if(archiveGood) else archiveErr
            parquetOut = parquetValue if(parquetGood) else parquetErr
            if (not interpGood): f.write("\nInterp: " + str(interpOut))
            if (not archiveGood): f.write("\nArchive: " + str(archiveOut))
            if (not parquetGood): f.write("\nParquet: " + str(parquetOut))
        raise Exception("One or more values are not correct")
else:
    print('Pi is a lie, skipping')
    
    
    
    

        
    
