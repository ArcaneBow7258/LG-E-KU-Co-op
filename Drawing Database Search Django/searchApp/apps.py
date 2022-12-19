from django.apps import AppConfig
from django.shortcuts import render
import io
import urllib, base64
import json
import time
import os
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
import os.path
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import open_dir


class SearchappConfig(AppConfig):
    name = 'searchApp'
    conf = SparkConf()
    conf.setAppName("QuestSearchTesting")
    conf.set('spark.jars', '/u00/spark/postgresql-42.2.9.jar')
    conf.set('spark.master', 'spark://dbsrv404.lgeenergy.int:7077')
    maxcores = 10
    conf.set('spark.cores.max', maxcores)
    conf.set('spark.executor.memory', '64g')
    conf.set('spark.driver.memory', '64g')
    conf.set('spark.executor.cores', 5)
    conf.set('spark.driver.maxResultSize', '64g')
    

    #Get text
    query1 = """select top(100) * from [Generation].[quest].[Drawings] WHERE DrawingTextAll IS NOT NULL"""
    queryProperties ={"user": "", "password": "", "driver":"org.postgresql.Driver","spark.jars":"file:/home/postgresTest/postgresql-42.2.9.jar","spark.executor.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar","spark.driver.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar", 'partitionColumn':'TAGID_PI', 'lowerBound': '1100000000' , 'upperBound': '1510890005', 'numPartitions':'80', 'fetchsize':'100000'}
    server = '' 
    database = '' 
    username = '' 
    password = ''
    cnxn = pyodbc.connect('DRIVER=/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.9.so.1.1;SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    #You may need to change the libmsodbcsql-17.8.s0.1.1 if we update it. Open a terminal cd out of /u01/ and start going down opt
    global questData
    questData = pd.read_sql(query1,cnxn)
    print("Data size: ", questData.count())
    cnxn.close()
    
    
    #Add documents to searcher
    schema = Schema(id = ID(stored=True), name=TEXT(stored=True), text=TEXT(stored=True))
    if not os.path.exists("documents"):
        os.mkdir("documents")
    global ix
    global writer
    ix = create_in("documents", schema)
    
    ix = open_dir("documents")
    writer = ix.writer()
    
    for index, row in questData.iterrows():
        writer.add_document(id = str(row.DrawingID).replace('-',' '), name = row.Name, text=row.DrawingTextAll)
    print('Documents added')
    writer.commit()
