#Import Libraries
import pyspark
import pyodbc
from pyspark import SparkContext, SparkConf
import sys
from pyspark.sql import DataFrameReader, SQLContext, SparkSession
from pyspark.sql.window import Window
from pyspark.sql.types import *
from pyspark.sql import functions as F
import pyspark.sql.functions as func
import numpy as np
import pandas as pd
import datetime as dt
import json
import getpass
from datetime import datetime, timedelta
import os.path

def extract(testSql, properties):
    df = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=testSql, properties=properties)
    df.printSchema()
    df.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
    #LOAD DATA
    df.count()
    #df.show()
    return df
props = {'user':'', 'password':'', 'driver':'org.postgresql.Driver', 'fetchsize':'100000'}

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
conf.set('spark.master', 'spark://dbsrv404.lgeenergy.int:7077')
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
TagQuery = f"(SELECT \"TAG_PI\",\"TAGID_PI\", \"LastInterpDateTime\" FROM \"PI\".\"PITAG\"  WHERE \"LastInterpDateTime\" > \'20220728 000000\') as a"
df_tags = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=TagQuery, properties=propertiesTAG)
tags_lst = df_tags.collect()
#tags_lst = list(pandas_tags['TAG_PI']) #Maybe change to TAGID_PI


#random
tag =  tags_lst[random.randint(0,len(tags_lst) - 1)]
targetTag = tag['TAG_PI']
targetID = tag['TAGID_PI']
startTime = datetime.strptime('2022-07-28 00:00:00',"%Y-%m-%d %H:%M:%S")
endTime = tag['LastInterpDateTime']
print("Range: ")
print(tag)
print(targetTag)
print(startTime)
print(endTime)
if (endTime > startTime):
    
    targetTime = endTime - timedelta(minutes = random.randint(0,(endTime-startTime).seconds//60))  - timedelta(seconds = endTime.second)
    print("Targets: ")
    print(targetTime)

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

    interpErr = ''

    interpValue = None

    margins = .1
    #Interp | InterpArchive | Parquet

    if(piGood):
        try:
            print('Interp')
            sql2 = f"(select tag,\"time\",value from \"PI\".\"PIInterp\"  WHERE tag = {targetID}  and \"time\" = \'{targetTime}\') as a"
            interpValue = extract(sql2,props)
            interpValue = interpValue.first()['value']
            print(interpValue)
            if(abs(piValue - float(interpValue))/piValue > margins):
                print('interp margins')
                interpGood = False
        except TypeError:
            print('Type error')
            interpErr = 'Interp or PI Gave me a None or Str value'
            interpGood = False
        except IndexError:
            print('index error')
            interpErr = 'Interp returned no value'
            interpGood = False
        except Exception as e:
            print('interp Error')
            interpGood = False
            interpErr = 'We did not check for: ' + str(e)
        if(not interpGood):
            print("OH NO SOMETHING WENT WRONG")
            with open(f'/u01/JupyterFolder/Test/Analysis/AlvinCode/DQA/DataQualityInterp{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}.txt', 'w') as f:
                f.write("Target Tag: " + targetTag)
                f.write("\nProbe Time: " + targetTime.strftime("%Y-%m-%d %H:%M:%S"))
                f.write("\nPi Value: " + str(piValue))
                interpOut = interpValue if(interpGood) else interpErr
                if (not interpGood): f.write("\nInterp: " + str(interpOut))
            raise Exception("One or more values are not correct")
    else:
        print('Pi is a lie, skipping')


else:
    print("Tag has not progressed")


        
    
