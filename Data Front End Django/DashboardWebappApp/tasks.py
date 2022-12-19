from django.apps import AppConfig
from django.shortcuts import render
import io
import urllib, base64
import json
import time
import os
import pyspark
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
import random
import datetime as dt

def append_latest_day():
    for index, partition in enumerate(brownTagList):
        brownInterpQuery = f"""(select *
                from "PI"."PIInterpArchive"
                where time > (current_date - INTERVAL '1 DAY')
                and time <= current_date
                and tag >= {partition[0]} and tag <= {partition[1]}
        ) as b"""
        brownInterpProperties={"user": "", "password": "", "driver":"org.postgresql.Driver","spark.jars":"file:/home/postgresTest/postgresql-42.2.9.jar",\
        "spark.executor.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar","spark.driver.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar", \
                'partitionColumn':'tag', 'lowerBound': f'{partition[0]}' , 'upperBound': f'{partition[1]}', 'numPartitions':'80', 'fetchsize':'100000'}
        chunk = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=brownInterpQuery, properties=brownInterpProperties)
        chunk.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        print("Brown Day Chunk {}: {}".format(index, chunk.count()))
        brownTagChunks[index].union(chunk)
    for index, partition in enumerate(caneRunTagList):
        caneRunInterpQuery = f"""(select *
                from "PI"."PIInterpArchive"
                where time > (current_date - INTERVAL '1 DAY')
                and time <= current_date
                and tag >= {partition[0]} and tag <= {partition[1]}
        ) as b"""
        caneRunInterpProperties={"user": "", "password": "", "driver":"org.postgresql.Driver","spark.jars":"file:/home/postgresTest/postgresql-42.2.9.jar",\
        "spark.executor.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar","spark.driver.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar", \
                'partitionColumn':'tag', 'lowerBound': f'{partition[0]}' , 'upperBound': f'{partition[1]}', 'numPartitions':'80', 'fetchsize':'100000'}
        chunk = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=caneRunInterpQuery, properties=caneRunInterpProperties)
        chunk.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        print("Cane Run Chunk {}: {}".format(index, chunk.count()))
        caneRunTagChunks[index].union(chunk)
    for index, partition in enumerate(ghentTagList):
        ghentInterpQuery = f"""(select *
                from "PI"."PIInterpArchive"
                where time > (current_date - INTERVAL '1 DAY')
                and time <= current_date
                and tag >= {partition[0]} and tag <= {partition[1]}
        ) as b"""
        ghentInterpProperties={"user": "", "password": "", "driver":"org.postgresql.Driver","spark.jars":"file:/home/postgresTest/postgresql-42.2.9.jar",\
        "spark.executor.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar","spark.driver.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar", \
                'partitionColumn':'tag', 'lowerBound': f'{partition[0]}' , 'upperBound': f'{partition[1]}', 'numPartitions':'80', 'fetchsize':'100000'}
        chunk = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=ghentInterpQuery, properties=ghentInterpProperties)
        chunk.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        print("Ghent Chunk {}: {}".format(index, chunk.count()))
        ghentTagChunks[index].union(chunk)
    for index, partition in enumerate(millCreekTagList):
        millCreekInterpQuery = f"""(select *
                from "PI"."PIInterpArchive"
                where time > (current_date - INTERVAL '1 DAY')
                and time <= current_date
                and tag >= {partition[0]} and tag <= {partition[1]}
        ) as b"""
        millCreekInterpProperties={"user": "", "": "", "driver":"org.postgresql.Driver","spark.jars":"file:/home/postgresTest/postgresql-42.2.9.jar",\
        "spark.executor.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar","spark.driver.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar", \
                'partitionColumn':'tag', 'lowerBound': f'{partition[0]}' , 'upperBound': f'{partition[1]}', 'numPartitions':'80', 'fetchsize':'100000'}
        chunk = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=millCreekInterpQuery, properties=millCreekInterpProperties)
        chunk.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        print("Mill Creek Chunk {}: {}".format(index, chunk.count()))
        millCreekTagChunks[index].union(chunk)
    for index, partition in enumerate(trimbleTagList):
        trimbleInterpQuery = f"""(select *
                from "PI"."PIInterpArchive"
                where time > (current_date - INTERVAL '1 DAYS')
                and time <= current_date
                and tag >= {partition[0]} and tag <= {partition[1]}
        ) as b"""
        trimbleInterpProperties={"user": "", "password": "", "driver":"org.postgresql.Driver","spark.jars":"file:/home/postgresTest/postgresql-42.2.9.jar",\
        "spark.executor.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar","spark.driver.extraClassPath":"/home/postgresTest/postgresql-42.2.9.jar", \
                'partitionColumn':'tag', 'lowerBound': f'{partition[0]}' , 'upperBound': f'{partition[1]}', 'numPartitions':'80', 'fetchsize':'100000'}
        chunk = DataFrameReader(sqlContext).jdbc(url='jdbc:%s' % url, table=trimbleInterpQuery, properties=trimbleInterpProperties)
        chunk.persist(storageLevel=pyspark.StorageLevel.MEMORY_ONLY)
        print("Trimble Chunk {}: {}".format(index, chunk.count()))
        trimbleTagChunks[index].union(chunk)
