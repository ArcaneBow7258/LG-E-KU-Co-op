from django.apps import AppConfig
from django.shortcuts import render
import io
import urllib, base64
import json
import time
import os
from os import listdir
from os.path import isfile, join
import shutil
import pyspark
import pyodbc
from pyspark import SparkContext, SparkConf
import sys

from pyspark.sql import DataFrameReader, SQLContext, SparkSession

from pyspark.sql.window import Window
from pyspark.sql.types import *

from pyspark.sql import functions as F
import pyspark.sql.functions as func
from pyspark.sql.functions import to_date
from pyspark.sql.functions  import date_format
from pyspark.sql.functions import col

import numpy as np
import pandas as pd
import datetime as dt
#import seaborn as sns

import random
import datetime as dt

from django.apps import AppConfig

from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso
import sklearn.metrics as metrics
import matplotlib.pyplot as plt

class DashboardwebappappConfig(AppConfig):
        
        #https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
        #credit where credit is due baby
        #print('removing csv files')
        csvPath = os.getcwd() + '/DashboardWebappApp/downloadCSV/'
        csvPandas = csvPath + 'Pandas/'
        onlyfiles = [ f for f in listdir(csvPandas)]
        for f in range(len(onlyfiles)):
            os.remove(csvPandas + onlyfiles[f])
            
        csvSpark = csvPath + 'Spark/'
        onlyfiles = [f for f in listdir(csvSpark)]
        for f in range(len(onlyfiles)):
            shutil.rmtree(csvSpark + onlyfiles[f])

        name = 'DashboardWebappApp'
        conf = SparkConf()
        conf.setAppName("PDWInterfaceTesting")
        conf.set('spark.jars', '/u00/spark/postgresql-42.2.9.jar')
        conf.set('spark.master', '')
        maxcores = 10
        conf.set('spark.cores.max', maxcores)
        conf.set('spark.executor.memory', '64g')
        conf.set('spark.driver.memory', '64g')
        conf.set('spark.executor.cores', 5)
        conf.set('spark.driver.maxResultSize', '64g')
        conf.set('spark.sql.session.timeZone', "America/New_York")
        sc = SparkContext.getOrCreate(conf=conf)
        sqlContext = SQLContext(sc)
        url = 'postgresql://localhost:5432/GENERATION'

        # Brown Tag Values - [1100000000,1111890003)
        # Ghent Tag Values - [1300000000,1304890030)
        # Mill Creek Tag Values - [1400000000,1404995745)
        # Trimble County Tag Values - [1500000000,1510890005)
        # Cane Run Tag Values - [1207000000,1207990008)
        tagQuery = """(select *
        from "PI"."PITAG"
        ) as b"""

        tagProperties = {"user": "", "password": "", "driver":"org.postgresql.Driver","spark.jars":"file:/home/postgresTest/postgresql-42.2.9.jar","spark.executor.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar","spark.driver.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar", 'partitionColumn':'TAGID_PI', 'lowerBound': '1100000000' , 'upperBound': '1510890005', 'numPartitions':'80', 'fetchsize':'100000'}
        #global tagData
        tagData = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=tagQuery, properties=tagProperties)
        tagData.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        tagData.count()

        # Hierarchy Data

        server = '' 
        database = '' 
        username = '' 
        password = ''

        query1 = """select ElementID, ParentElementID, Element, Template from [Generation].[agent].[AF_Hierarchy]"""

        query2 = """select a.ElementID, ParentElementID, Element, AttributeName, pitag, att_description, fullpath
                        from [Generation].[agent].[AF_Hierarchy] as a inner join [Generation].[agent].[AF_Attributes] as b on (a.ElementID = b.ElementID)
                        where b.pitag2 is not null and pitag != ''"""

        #cnxn = pyodbc.connect('DRIVER=/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.9.so.1.1;SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
        #You may need to change the libmsodbcsql-17.8.s0.1.1 if we update it. Open a terminal cd out of /u01/ and start going down opt
        #global elements
        #elements = pd.read_sql(query1,cnxn)
        #global attributes
        #attributes = pd.read_sql(query2,cnxn)
        #cnxn.close()

        # Brown

        global brownMinimumTag
        brownMinimumTag = 1100000000
        brownMaximumTag = 1111890003

        global brownTagData
        brownTagData = tagData.filter((tagData.TAGID_PI >= brownMinimumTag) & (tagData.TAGID_PI <= brownMaximumTag))
        brownTagData.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        brownTagData.count()

        # global brownData
        # brownData = {}

        # brownData["U0"] = sqlContext.read.parquet('/u01/productiondata/brown2020_U0.parquet')
        # brownData["U0"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Brown Unit 0 Count:", brownData["U0"].count())

        # sqlContext = SQLContext(sc)
        # brownData["U3"] = sqlContext.read.parquet('/u01/productiondata/brown2020_U3.parquet')
        # brownData["U3"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Brown Unit 3 Count:", brownData["U3"].count())

        # brownData["U5"] = sqlContext.read.parquet('/u01/productiondata/brown2020_U5.parquet')
        # brownData["U5"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Brown Unit 5 Count:", brownData["U5"].count())

        # brownData["U6"] = sqlContext.read.parquet('/u01/productiondata/brown2020_U6.parquet')
        # brownData["U6"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Brown Unit 6 Count:", brownData["U6"].count())

        # brownData["U7"] = sqlContext.read.parquet('/u01/productiondata/brown2020_U7.parquet')
        # brownData["U7"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Brown Unit 7 Count:", brownData["U7"].count())

        # brownData["U8"] = sqlContext.read.parquet('/u01/productiondata/brown2020_U8.parquet')
        # brownData["U8"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Brown Unit 8 Count:", brownData["U8"].count())

        # brownData["U9"] = sqlContext.read.parquet('/u01/productiondata/brown2020_U9.parquet')
        # brownData["U9"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Brown Unit 9 Count:", brownData["U9"].count())

        # brownData["U10"] = sqlContext.read.parquet('/u01/productiondata/brown2020_U10.parquet')
        # brownData["U10"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Brown Unit 10 Count:", brownData["U10"].count())

        # brownData["U11"] = sqlContext.read.parquet('/u01/productiondata/brown2020_U11.parquet')
        # brownData["U11"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Brown Unit 11 Count:", brownData["U11"].count())

        # CaneRun

        global canerunMinimumTag
        canerunMinimumTag = 1207000000
        canerunMaximumTag = 1207990008

        global canerunTagData
        canerunTagData = tagData.filter((tagData.TAGID_PI >= canerunMinimumTag) & (tagData.TAGID_PI <= canerunMaximumTag))
        canerunTagData.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        canerunTagData.count()

        # global canerunData
        # canerunData = {}
        # canerunData["U7"] = sqlContext.read.parquet('/u01/productiondata/canerun2020_U7.parquet')
        # canerunData["U7"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("CaneRun Unit 7 Count:", canerunData["U7"].count())

        # # Ghent

        global ghentMinimumTag
        ghentMinimumTag = 1300000000
        ghentMaximumTag = 1304890030

        global ghentTagData
        ghentTagData = tagData.filter((tagData.TAGID_PI >= ghentMinimumTag) & (tagData.TAGID_PI <= ghentMaximumTag))
        ghentTagData.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        ghentTagData.count()

        #global ghentData
        #ghentData = {}
        
        #rRange = []
        #for i in [8,42]:
        #    ghentData[f"U1C{i}"] = sqlContext.read.parquet(f'/u01/JupyterFolder/Production/Parquet/ghent_U1_Core_{i:02d}.parquet')
         #   ghentData[f"U1C{i}"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
         #   print(f"Ghent Unit 1 Core Count U1C{i}:", ghentData[f"U1C{i}"].count())
        # ghentData["U0"] = sqlContext.read.parquet('/u01/productiondata/ghent2020_U0.parquet')
        # ghentData["U0"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Ghent Unit 0 Count:", ghentData["U0"].count())

        # ghentData["U1"] = sqlContext.read.parquet('/u01/productiondata/ghent2020_U1.parquet')
        # ghentData["U1"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Ghent Unit 1 Count:", ghentData["U1"].count())

        # ghentData["U2"] = sqlContext.read.parquet('/u01/productiondata/ghent2020_U2.parquet')
        # ghentData["U2"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Ghent Unit 2 Count:", ghentData["U2"].count())

        # ghentData["U3"] = sqlContext.read.parquet('/u01/productiondata/ghent2020_U3.parquet')
        # ghentData["U3"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Ghent Unit 3 Count:", ghentData["U3"].count())

        # ghentData["U4"] = sqlContext.read.parquet('/u01/productiondata/ghent2020_U4.parquet')
        # ghentData["U4"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("Ghent Unit 4 Count:", ghentData["U4"].count())

        # # Mill Creek

        global millcreekMinimumTag
        millcreekMinimumTag = 1400000000
        millcreekMaximumTag = 1404995745

        global millcreekTagData
        millcreekTagData = tagData.filter((tagData.TAGID_PI >= millcreekMinimumTag) & (tagData.TAGID_PI <= millcreekMaximumTag))
        millcreekTagData.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        millcreekTagData.count()

        # global millcreekData
        # millcreekData = {}

        # millcreekData["U0"] = sqlContext.read.parquet('/u01/productiondata/millcreek2020_U0.parquet')
        # millcreekData["U0"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("MillCreek Unit 0 Count:", millcreekData["U0"].count())

        # millcreekData["U1"] = sqlContext.read.parquet('/u01/productiondata/millcreek2020_U1.parquet')
        # millcreekData["U1"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("MillCreek Unit 1 Count:", millcreekData["U1"].count())

        # millcreekData["U2"] = sqlContext.read.parquet('/u01/productiondata/millcreek2020_U2.parquet')
        # millcreekData["U2"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("MillCreek Unit 2 Count:", millcreekData["U2"].count())

        # millcreekData["U3"] = sqlContext.read.parquet('/u01/productiondata/millcreek2020_U3.parquet')
        # millcreekData["U3"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("MillCreek Unit 3 Count:", millcreekData["U3"].count())

        # millcreekData["U4"] = sqlContext.read.parquet('/u01/productiondata/millcreek2020_U4.parquet')
        # millcreekData["U4"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        # print("MillCreek Unit 4 Count:", millcreekData["U4"].count())

        # Trimble

        global trimbleMinimumTag
        global trimbleMaximumTag
        trimbleMinimumTag = 1500000000
        trimbleMaximumTag = 1510890005

        global trimbleTagData
        trimbleTagData = tagData.filter((tagData.TAGID_PI >= trimbleMinimumTag) & (tagData.TAGID_PI <= trimbleMaximumTag))
        trimbleTagData.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        trimbleTagData.count()

        #global trimbleData
        #trimbleData = {}

        #rRange = [15,23,89]
        #for i in range(15, 24, 8):
        #for i in range(0, 90):
        #for i in [15,23,89]:
        #    trimbleData[f"U1C{i}"] = sqlContext.read.parquet(f'/u01/JupyterFolder/Production/Parquet/trimble_U1_Core_{i:02d}.parquet')
         #   trimbleData[f"U1C{i}"].persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        #    print(f"Trimble Unit 1 Core Count U1C{i}:", trimbleData[f"U1C{i}"].count())
        
        # global brownTags
        # brownTags = list(map(lambda x: (x['TAG_PI'], x['descriptor']), brownTagData.select("TAG_PI", "descriptor").distinct().orderBy("TAG_PI").collect()))
        # global canerunTags
        # canerunTags = list(map(lambda x: (x['TAG_PI'], x['descriptor']), canerunTagData.select("TAG_PI", "descriptor").distinct().orderBy("TAG_PI").collect()))
        # global ghentTags
        # ghentTags = list(map(lambda x: (x['TAG_PI'], x['descriptor']), ghentTagData.select("TAG_PI", "descriptor").distinct().orderBy("TAG_PI").collect()))
        # global millcreekTags
        # millcreekTags = list(map(lambda x: (x['TAG_PI'], x['descriptor']), millcreekTagData.select("TAG_PI", "descriptor").distinct().orderBy("TAG_PI").collect()))
        #global trimbleTags
        #trimbleTags = list(map(lambda x: (x['TAG_PI'], x['descriptor']), trimbleTagData.select("TAG_PI", "descriptor").distinct().orderBy("TAG_PI").collect()))
