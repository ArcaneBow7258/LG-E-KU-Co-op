import pyspark
from pyspark import SparkContext, SparkConf
import sys
import os
import time
import decimal
from datetime import datetime, timedelta

from pyspark.sql.types import *
from pyspark.sql.functions import to_date
from pyspark.sql.functions  import date_format

import re

from pyspark.mllib.stat import KernelDensity
from array import array
import numpy as np
import pandas as pd

import pyspark.sql.functions as func
from pyspark.sql import Window
from pyspark.sql import DataFrameReader, SQLContext, SparkSession
from pyspark.sql.functions import pandas_udf, PandasUDFType
#from pyspark.sql.functions import col, collect_list, concat_ws, udf, lit
from pyspark.sql.functions import col, row_number, collect_list, concat_ws, udf, lit, lower
import pytz

#print(datetime.now())

conf = SparkConf().setMaster("")
try:
    conf.setAppName("InterpForward" +  str(sys.argv[3]))
except:
    conf.setAppName("InterpForward")

sc = SparkContext(conf=conf)
sqlContext = SQLContext(sc)
spark = SparkSession(sc)
url = 'postgresql://localhost:5432/GENERATION'


#pulls data from postgress and persists into memory
def extract(testSql, properties):
    df = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=testSql, properties=properties)
    df.printSchema()
    df.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
    #LOAD DATA
    df.count()
    df.show()
    return df


@udf(ArrayType(DecimalType(38,18)))
def interpolate(bigList,step):
    minDate = bigList[0]["collect_list(TIME_PI)"]+timedelta(minutes=1)
    minDate=str(minDate)[:17]+'00'
    maxDate = str(bigList[-1]["collect_list(TIME_PI)"])[:17]+'00'
    if step:
        maxDate = highQuery
    Clist = list(pd.date_range(start=minDate, end=maxDate, freq='min'))
    idx = [0]*(len(Clist))
    for i in range(len(idx)):
        #print('i = ',i)
        #print('range for j',range(idx[i-1],len(bigList)-1))
        for j in range(idx[i-1],len(bigList)-1):
            #print('j = ',j)
            #print('this should be <=',bigList[j]["collect_list(TIME_PI)"])
            #print('this value',Clist[i])
            #print('this should be > the previous value',bigList[j+1]["collect_list(TIME_PI)"])
            if bigList[j]["collect_list(TIME_PI)"] <= Clist[i] and bigList[j+1]["collect_list(TIME_PI)"]>Clist[i]:
                #print('setting new idx')
                idx[i]=j
                #print('idx = ',idx)
                break
            elif step and bigList[j+1]["collect_list(TIME_PI)"]<=Clist[i] and len(bigList)-1==(j+1): 
                #print('this value',bigList[j+1]["collect_list(TIME_PI)"])
                #print('<= this value',Clist[i])
                idx[i:]=[j+1]*len(idx[i:])
                #print('new step scenario')
                #print('idx = ',idx)
                break
            if i==(len(idx)-1) and bigList[j+1]["collect_list(TIME_PI)"]==Clist[i]:
                idx[i]=j+1
                #print('last value exception')
                #print('idx = ',idx)
    values = []
    if step:
        for i in range(len(idx)):
            values.append(bigList[idx[i]]["collect_list(VALUE_PI)"])
    else:
        for i in range(len(idx)):
            if idx[i]+1<len(bigList):
                if bigList[idx[i]+1]["collect_list(dTime)"] != -99999 and bigList[idx[i]+1]["collect_list(dVal)"] != -99999 and bigList[idx[i]+1]["collect_list(dTime)"] != 0:
                    d = (Clist[i]-bigList[idx[i]]["collect_list(TIME_PI)"]).total_seconds()
                    d = d/bigList[idx[i]+1]["collect_list(dTime)"]
                    d = decimal.Decimal(d)*bigList[idx[i]+1]["collect_list(dVal)"]
                    d = d+bigList[idx[i]]["collect_list(VALUE_PI)"]
                    values.append(d)
                else:
                    d=decimal.Decimal(-99999)
                    values.append(d)
            elif (idx[i]+1==len(bigList)) and (bigList[idx[i]]["collect_list(TIME_PI)"]==Clist[i]):
                values.append(bigList[idx[i]]["collect_list(VALUE_PI)"])
    return values

@udf("float")
def diff(date1,date2):
    if date2:
        return date1.timestamp()-date2.timestamp()
    else:
        return None

@udf("array<timestamp>")
def C(bigList,step):
    minDate = bigList[0]["collect_list(TIME_PI)"]+timedelta(minutes=1)
    minDate=str(minDate)[:17]+'00'
    maxDate = str(bigList[-1]["collect_list(TIME_PI)"])[:17]+'00'
    if step:
        maxDate = highQuery
    Clist = list(pd.date_range(start=minDate, end=maxDate, freq='min'))
    return Clist


#NORMAL USE
lowTag = str(sys.argv[1])
highTag = str(sys.argv[2])
filename = str(sys.argv[3])
#lowQuery = str(datetime.strptime(str(sys.argv[4]), '%Y-%m-%d %H:%M:%S'))
#highQuery = str(datetime.strptime(str(sys.argv[5]), '%Y-%m-%d %H:%M:%S'))
lowDateTime = datetime.strptime(str(sys.argv[4]), '%Y-%m-%d %H:%M:%S')
lowQuery =  str(lowDateTime.astimezone(pytz.timezone('EST')).strftime('%Y-%m-%d %H:%M:%S')) #Converting from ET to UTC then to EST 
#print(lowQuery)
highDateTime = datetime.strptime(str(sys.argv[5]), '%Y-%m-%d %H:%M:%S')
highQuery = str(highDateTime.astimezone(pytz.timezone('EST')).strftime('%Y-%m-%d %H:%M:%S')) #Converting from ET to UTC then to EST 
partitions='80'
##FOR TESTING
#lowQuery = '2022-07-28 00:00:00'
#highQuery = '2022-07-28 00:10:00'
#partitions='80'
#lowTag = '1300000000'#'1207000006'#
#highTag = '1400000000'#'1207000006'#
#filename = 'ghent20220728T010000-20220728T011000.csv'
#filename = 'ghent20220728T011000-20220728T012000.csv'

#print(datetime.now())
print('lowtag: ',lowTag)
print('hightag: ',highTag)
print('filename: ',filename)
print('lowQuery: ',lowQuery)
print('highQuery: ',highQuery)

schema = StructType([
    StructField("TAG_PI", StringType(), True),
    StructField("TIME_PI", TimestampType(), True),
    StructField("VALUE_PI", DecimalType(38,18), True),
    StructField("SVALUE_PI", StringType(),True),
    StructField("STATUS_PI", StringType(),True),
    StructField("FLAGS_PI", StringType(),True)])
#A=spark.read.csv(f"{filename}",header=False,sep = ';',schema=schema) #use for debugging
A=spark.read.csv(f"/u00/{filename}",header=False,sep = ';',schema=schema) #use for production
props2 = {'user':'', 'password':'', 'driver':'org.postgresql.Driver', 'partitionColumn':'TAGID_PI', 'lowerBound': lowTag , 'upperBound': highTag, 'numPartitions':partitions, 'fetchsize':'100000'}
sql2 = f"(select \"TAGID_PI\",\"TAG_PI\",\"LastInterpDateTime\", \"LastInterpValue\",\"IsStep\" ,\"digitalset\" from \"PI\".\"PITAG\" WHERE \"TAGID_PI\" >= {lowTag} and \"TAGID_PI\" <= {highTag} and \"isDead\" = False and \"IsInterp\" is true) as a"
previousTimes = extract(sql2,props2)

#with open(re.findall(r"^\D+", filename)[0] + 'CompInterpCSV.txt', 'w') as f:
#    f.write('RUN ' + str(datetime.now()) + '\n')
#    f.write(' '.join(['DATA IMPORTED', lowQuery, highQuery, lowTag, highTag]) + '\n')


#join to get TAGID
A=A.join(previousTimes,lower(A['TAG_PI'])== lower(previousTimes['TAG_PI']),"inner").drop(A['TAG_PI'])
CompressedData = A.select("TAGID_PI","TIME_PI","VALUE_PI","SVALUE_PI","STATUS_PI","FLAGS_PI")

NewTimes=A.where("IsStep == False").groupby('TAGID_PI').agg({'TIME_PI':'max'}).withColumnRenamed("TAGID_PI", "tagid")
NewTimes=NewTimes.join(A,(A["TIME_PI"]==NewTimes["max(TIME_PI)"]) & (A["TAGID_PI"]==NewTimes["tagid"])).drop(NewTimes["tagid"]).drop(NewTimes["max(TIME_PI)"])
NewTimes=NewTimes.select("TAGID_PI","TIME_PI","VALUE_PI").withColumn("FileName",lit(filename))

A=A.filter(A.LastInterpDateTime.isNotNull())
A=A.withColumn('VALUE_PI', func.when((A.VALUE_PI < 0.00000000000001)&(A.VALUE_PI > -0.00000000000001), 0).otherwise(A.VALUE_PI)) 
A=A.withColumn('VALUE_PI', func.when(((A.VALUE_PI/1000000000000000000)>=1)|((A.VALUE_PI/-1000000000000000000)<=-1), None).otherwise(A.VALUE_PI))
A=A.select(A.TAGID_PI,A.TIME_PI,A.VALUE_PI,A.SVALUE_PI,A.IsStep,A.digitalset)

#string processing
#A=A.withColumn("VALUE_PI", stringConvert(A.VALUE_PI, A.SVALUE_PI, A.digitalset))
A=A.drop("SVALUE_PI", "digitalset")
A=A.withColumn('VALUE_PI', A.VALUE_PI.cast(DecimalType(38,18)))
previousTimes = previousTimes.drop('digitalset')

previousTimes=previousTimes.withColumnRenamed('LastInterpDateTime','TIME_PI').withColumnRenamed('LastInterpValue','VALUE_PI').drop(previousTimes['TAG_PI'])
stepTags = previousTimes[previousTimes.IsStep==True].drop("TIME_PI","VALUE_PI","IsStep")
uniqueTags=A.drop("TIME_PI","VALUE_PI","IsStep").union(stepTags).distinct()
EndCompTime = uniqueTags.join(previousTimes, previousTimes["TAGID_PI"]==uniqueTags["TAGID_PI"]).drop(uniqueTags["TAGID_PI"])
A = A.union(EndCompTime).orderBy('TAGID_PI','TIME_PI') 

mywindow = Window.partitionBy("TAGID_PI").orderBy("TIME_PI")

#union
A = A.withColumn("prevtime", func.lag(A.TIME_PI).over(mywindow)).withColumn("prevval", func.lag(A.VALUE_PI).over(mywindow))
A = A.withColumn("dTime",diff("TIME_PI", "prevtime")).drop("prevtime").withColumn("dVal",func.col("VALUE_PI")-func.col("prevval")).drop("prevval")

enoughValues = A.groupBy("TAGID_PI","IsStep").max("dTime")
enoughValues = enoughValues.where(("max(dTime) IS NOT NULL OR IsStep == True"))  #only keeping tags where there are two or more values, or it's a step tag
A = A.join(enoughValues, A.TAGID_PI == enoughValues.TAGID_PI ,"inner").select(A["*"])


A = A.fillna(-99999)

A = A.sort("TAGID_PI","TIME_PI").groupBy("TAGID_PI","IsStep").agg(collect_list("TIME_PI"),collect_list("VALUE_PI"),collect_list("dTime"),collect_list("dVal")) 
A = A.where(func.size(A['collect_list(TIME_PI)'])!= 0)##filtering out tags where there are no values at all
A =A.select(func.arrays_zip(func.col("collect_list(TIME_PI)"),func.col("collect_list(VALUE_PI)"),func.col("collect_list(dTime)"),func.col("collect_list(dVal)")).alias("bigList"),
"TAGID_PI","IsStep")


#bigList=A.first()['bigList']
#step = A.first()['IsStep']
#bigList = A.select('bigList').collect()[25][0]
#step = A.select('IsStep').collect()[25][0]   
#B = A.filter(A.TAGID_PI == 1301280047)
#bigList = B.select('bigList').collect()[0][0]
#with open(re.findall(r"^\D+", filename)[0] + 'CompInterpCSV.txt', 'a') as f:
#    f.write('Interp Start \n')
  
IValues = A.withColumn("interp",interpolate(func.col("bigList"),func.col("IsStep")))

#IValues.filter(IValues.TAGID_PI == 1207080029).show(200)
#IValues.filter(IValues.TAGID_PI == 1207080029).select('bigList').collect()

IValues = IValues.withColumn("C",C("bigList","IsStep"))
IValues = IValues.withColumn("combo",func.arrays_zip("interp","C"))
IValues = IValues.select(func.explode(func.col("combo")).alias("temp"),"TAGID_PI","IsStep")
IValues = IValues.select(func.col("temp")["interp"].alias("IValue"),func.col("temp")["C"].alias("Time"),"TAGID_PI","IsStep")
IValues = IValues.orderBy("TAGID_PI", "time")
IValues = IValues.replace(-99999,None)
IValues = IValues.filter(IValues.Time.isNotNull()).withColumnRenamed("Time", "TIME_PI")

#IValues.filter(IValues.TAGID_PI == 1207010006).show(200)

mywindow = Window.partitionBy("TAGID_PI").orderBy(col("TIME_PI").desc())
stepTags = IValues.where("IsStep == True").withColumn("row",row_number().over(mywindow)).filter(col("row") == 1).drop("row")
stepTags = stepTags.withColumnRenamed("IValue", "VALUE_PI").select("TAGID_PI","TIME_PI","VALUE_PI").withColumn("FileName",lit(filename))
NewTimes = NewTimes.union(stepTags)
#with open(re.findall(r"^\D+", filename)[0] + 'CompInterpCSV.txt', 'a') as f:
#    f.write('Data write start \n')
dfInter = IValues.withColumnRenamed("IValue", "value").withColumnRenamed("TIME_PI","time").withColumnRenamed("TAGID_PI","tag").drop("IsStep")
dfInter.count()
#dfInter.show()
#print(datetime.now())

#print(datetime.now())
dfInter.toPandas().to_csv(f"/u00/interp-{filename}", sep=';', header=False, index=False) 
print('Wrote to /u00/interp-',filename)
#print(datetime.now())
#InterpValues = {'user':'', 'password':'?', 'driver':'org.postgresql.Driver', 'partitionColumn':'tag', 'lowerBound': lowTag , 'upperBound': highTag, 'numPartitions':partitions, 'batchsize':'1000000'} #1000000
#dfInter.write.jdbc(url='jdbc:%s' % url,table="\"PI\".\"PIInterpRYAN\"",mode='append',properties=InterpValues)#append
#print(datetime.now())

#print(datetime.now())
NewTimes.toPandas().to_csv(f"/u00/latestCompressed-{filename}", sep=';', header=False, index=False) 
#LatestPoints = {'user':'', 'password':'?', 'driver':'org.postgresql.Driver', 'partitionColumn':'TAGID_PI', 'lowerBound': lowTag , 'upperBound': highTag, 'numPartitions':partitions, 'fetchsize':'100000'}
#NewTimes.write.jdbc(url='jdbc:%s' % url,table="\"PI\".\"LatestCompressedTimes\"",mode='append',properties=LatestPoints)#append
print('Wrote to LastCompressedTimes')

#print(datetime.now())
CompressedData.toPandas().to_csv(f"/u00/comp-{filename}", sep=';', header=False, index=False) 
print('Wrote to /u00/comp-',filename)
#CompValues = {'user':'', 'password':'?', 'driver':'org.postgresql.Driver', 'partitionColumn':'TAGID_PI', 'lowerBound': lowTag , 'upperBound': highTag, 'numPartitions':partitions, 'fetchsize':'100000'}
#CompressedData.write.jdbc(url='jdbc:%s' % url,table="\"PI\".\"PIRYAN\"",mode='append',properties=CompValues)#append
#print(datetime.now())
#with open(re.findall(r"^\D+", filename)[0] + 'CompInterpCSV.txt', 'a') as f:
#    f.write('End of Script\n')
#print(sTime)
#print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print('COMPLETELY FINISHED')
