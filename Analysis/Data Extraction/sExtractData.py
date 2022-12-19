from requests.auth import HTTPBasicAuth
import requests
import json
import pyspark
from pyspark import SparkContext, SparkConf
from pyspark.sql import DataFrameReader, SQLContext, SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from multiprocessing import Process, Queue
from multiprocessing import Pool, TimeoutError
from datetime import datetime, timedelta
import time
import urllib3
from pytz import timezone, all_timezones
urllib3.disable_warnings()
CONFIG = {'PIWEBAPI_URL' : '',
            'SERVER' : '',
            'SECURITY_METHOD' : 'basic',
            'USER' : '',
            'PASSW' : '', #
            'VERIFY_SSL' : False}
postgresUrl = 'postgresql://localhost:5432/GENERATION'

def call_security_method(security_method, user_name, user_password):
    
    if security_method.lower() == 'basic':
        security_auth = HTTPBasicAuth(user_name, user_password)
        
    return security_auth
def getRequest(urlString): 
    security_auth = call_security_method(CONFIG['SECURITY_METHOD'], CONFIG['USER'], CONFIG['PASSW'])
    response = requests.get(urlString, auth=security_auth, verify=CONFIG['VERIFY_SSL'])
    return response


conf = SparkConf().setMaster("spark://dbsrv404.lgeenergy.int:7077")
conf.set('spark.jars', '/u00/spark/postgresql-42.2.9.jar')
conf.set('spark.master', 'spark://dbsrv404.lgeenergy.int:7077')
conf.setAppName('ExtractDataSpark')
conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
maxcores = 5
conf.set('spark.cores.max', maxcores)
conf.set('spark.executor.memory', '64g')
conf.set('spark.driver.memory', '64g')
conf.set('spark.executor.cores', 5)

sc = SparkContext(conf=conf)
spark = SparkSession(sc)

def sExtractParquet(file, tags, start, end):
    sparkdata = spark.read.parquet(file)

    
    sparkdata = sparkdata.filter((sparkdata.time > start) & (sparkdata.time < end) & (sparkdata.tag.isin(tags)))
    print(sparkdata.count())
    return sparkdata
def sDriverParquet(parquetFiles, start, end):
    
    df = spark.createDataFrame(data = spark.sparkContext.emptyRDD(), schema = StructType([StructField("tag", StringType(), False),
                                                                                                StructField('time', TimestampType(), False),
                                                                                                StructField('value', DecimalType(), True)
    ]))

    
    
    for file in parquetFiles:
        df = df.union(sExtractParquet(file, parquetFiles[file], start, end))

    return df

def sExtractPostgres(query):
    sparkdata = spark.read.format('jdbc').option('url', postgresUrl).option('driver','org.postgresql.Driver').option('user','APP1206').option('password','?')
    sparkdata = sparkdata.jdbc('jdbc:'+postgresUrl,f'({query}) as reallyUglyNameSoNoOneAccidentlyPutsSameThing')
    return sparkdata

@udf("float")
def WebAPIList(value, good):
    if good:
        try:
            return value['Value']
        except:
            return value
    else:
        return None
def sExtractWebAPI(tagID, start, end,  interp = True, interval = '1m'):
    rowSum=int((end-start).total_seconds()/60)
    loopData = spark.createDataFrame(data = spark.sparkContext.emptyRDD(), schema = StructType([StructField("tag", StringType(), False),
                                                                                                StructField('time', TimestampType(), False),
                                                                                                StructField('value', DecimalType(), True)
    ]))
    #print('rowSum = ',rowSum)
    increment = 120000 
    
    for i in range(0, rowSum, increment):
        thisLoopStart = (start+timedelta(seconds=(60*i))).strftime("%Y-%m-%d %H:%M:%S")
        #print('loop start=',i)
        if i+increment-1<rowSum:
            thisLoopStop = (start+timedelta(seconds=(60*(i+increment-1)))).strftime("%Y-%m-%d %H:%M:%S")
            #print('loop end =',i+increment-1)
        else:
            thisLoopStop = end.strftime("%Y-%m-%d %H:%M:%S")
            #print('loop end =',rowSum)
        
        #print('start time =',thisLoopStart)
        #print('end time =',thisLoopStop)
        getDatabaseQuery = f"{CONFIG['PIWEBAPI_URL']}?path=\\PIServers[{CONFIG['SERVER']}]" #databasePath = "\\\\PIServers[]"
        responseWebID = getRequest(getDatabaseQuery)
        if responseWebID.status_code == 200:

            database = json.loads(responseWebID.text)
            WebID = database['WebId']
            
            metaDataURL = f"{CONFIG['PIWEBAPI_URL']}/{WebID}/points?nameFilter={tagID}"
            responseMetaData = getRequest(metaDataURL)
            
            if responseMetaData.status_code == 200:
                
                tagMetaData = json.loads(responseMetaData.text)
                if len(tagMetaData['Items']) > 0:
                    dataLink = tagMetaData['Items'][0]['Links']['InterpolatedData']
                    timeFilter = f"?starttime={thisLoopStart.replace(' ','%20')}&endtime={thisLoopStop.replace(' ','%20')}&interval={interval}"
                    
                    if interp == False:
                        dataLink = tagMetaData['Items'][0]['Links']['RecordedData']
                        timeFilter = f"?starttime={thisLoopStart.replace(' ','%20')}&endtime={thisLoopStop.replace(' ','%20')}"

                    dataLink = dataLink+timeFilter
                    responseDataString = getRequest(dataLink)
                    if responseDataString.status_code == 200:

                        dataString = responseDataString.text
                        
                        dataSubString = dataString[dataString.index('['):dataString.index(']')+1]
                        
                        df = spark.read.option("multiline","true").json(sc.parallelize([dataSubString]))
                        df = df.withColumn("tag",lit(tagID)).withColumn('time', df.Timestamp)
                        df = df.withColumn("time", df['TimeStamp'])
                        df = df.withColumn('value', WebAPIList(df.Value, df.Good))
                        df = df['tag', 'time', 'value']
                        df=df.withColumn('value', df.value.cast(DecimalType(38,18)))
    
                        if time.localtime().tm_isdst == 0:
                            df = df.withColumn('time', to_utc_timestamp('time', "UTC"))
                        else:
                            df = df.withColumn('time', to_utc_timestamp('time', "UTC") - expr("interval 1 hour"))
                    else:
                        return f"API Call Failed at Data String Level. Status code {responseDataString.status_code}"
                     
                else:
                    return "Tag Not Found"
                   
            else:
                return f"API Call Failed at Meta Data Level. Status code {responseMetaData.status_code}"
              
        else:
            return f"API Call Failed at Element Web ID Level. Status code {responseWebID.status_code}"
           
        #print(data)
        loopData = loopData.union(df)
        
    return loopData
   
        

def sDriverWebAPI(tagIDs, start, end, interp = True, interval = '1m'):
    df = spark.createDataFrame(data = spark.sparkContext.emptyRDD(), schema = StructType([StructField("tag", StringType(), False),
                                                                                                StructField('time', TimestampType(), False),
                                                                                                StructField('value', DecimalType(), True)
    ]))

    for tag in tagIDs:
        df=df.union(sExtractWebAPI(tag,start,end,interp, interval))

    return df
