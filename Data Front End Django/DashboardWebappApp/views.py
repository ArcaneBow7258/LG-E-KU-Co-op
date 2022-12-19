from django.shortcuts import render
import io
import urllib, base64
import json
import time
import os
import pyspark
from pyspark import SparkContext, SparkConf
import sys
from pyspark.sql.types import StructType,StructField, StringType
from pyspark.sql import DataFrameReader, SQLContext, SparkSession 
from pyspark.sql.window import Window
from pyspark.sql.types import *

from pyspark.sql import functions as F
import pyspark.sql.functions as func
from pyspark.sql.functions import to_date
from pyspark.sql.functions  import date_format
from pyspark.sql.functions import col
from pyspark.sql.functions import lower
from pyspark.ml.feature import MinMaxScaler
from pyspark.sql.functions import collect_list

import numpy as np
import pandas as pd
import datetime as dt
import seaborn as sns

import random
import datetime as dt
from DashboardWebappApp.apps import *
from django.http import HttpResponse
from decimal import Decimal
from pyspark.sql import functions as F
sys.path.insert(1,'/u01/JupyterFolder/Test/Analysis')
from ExtractPIData import *
from DashboardWebappApp.models import Account
from DashboardWebappApp.models import TagSet
from django.db.models.query import EmptyQuerySet
from DashboardWebappApp.models import TagRequest
# Create your views here.

def timeSeries(request):
	return render(request, 'timeSeries.html')
def trends(request):
	return render(request, 'regressionPage.html')
def explore(request):
	return render(request, 'matrix.html')
def searchPage(request):
    return render(request, "searchPage.html")
def aboveBelow(request):
    return render(request, "aboveBelow.html")
def requestPage(request):
    return render(request, "requestPage.html")
#maybe aggreagate this into getTagSet
#and saveTagSet
def requestRequests(request):
    all_entries = list(TagRequest.objects.all())
    #Gets all objects as list, although list is of attributes <TagSet>
    #Converting them all into a list of dictionaries to return as a json
    all_entries = list(map(lambda x: x.__dict__, all_entries))
    #Doing this way as using TagSet.object.values() gives us that weird "QuerySet" text which isn't a straight Array of Dicts we want
    js_data = json.dumps(all_entries, default = str)
    return HttpResponse(js_data)
def newRequest(request):
    tag = request.POST['tagName']
    try: 
        requery = TagRequest.objects.get(tagName = tag)
        requery.LastRequestDate = request.POST['time']
        requery.save()
        return HttpResponse('Update Request')
    except:
        req = TagRequest(tagName = request.POST['tagName'],
                        InitialRequestDate = request.POST['time'],
                        LastRequestDate =  request.POST['time']
                        )
        req.save()
        return HttpResponse('New Request')

def preprocess(request):
        requestInformation = {}
        plant = request.POST['plant']
        info = json.dumps(reqftInformation, default=str)
        return HttpResponse(info)
def useTagSet(request):
    tagQuery = TagSet.objects.get(tags = request.POST['tags'])
    #Since we're grabbing name from an actualy TagSet we loaded, we know it exists
    tagQuery.lastUsed = request.POST['lastUsed']
    tagQuery.save()
    return HttpResponse()
def saveTagSet(request):
    try: 
        tagQuery = TagSet.objects.get(tags = request.POST['tags'])
        return HttpResponse("Tags are already saved under " + str(tagQuery.name))
        
    except:
        print("Empty! Good to go!")
        newSet = TagSet(filePath = request.POST['filePath'],
                        name = request.POST['name'],
                        fullPath =  request.POST['filePath'] + '/' + request.POST['name'],
                        tags = request.POST['tags'], 
                        plants = request.POST['plants'], 
                        minTime = request.POST['minTime'], 
                        maxTime = request.POST['maxTime'],
                        lastUpdated = request.POST['lastUpdated'],
                        lastUsed = None)
        newSet.save()
        return HttpResponse()
        
    
def getTagSet(request):
    all_entries = list(TagSet.objects.all())
    #Gets all objects as list, although list is of attributes <TagSet>
    #Converting them all into a list of dictionaries to return as a json
    all_entries = list(map(lambda x: x.dict(), all_entries))
    #Doing this way as using TagSet.object.values() gives us that weird "QuerySet" text which isn't a straight Array of Dicts we want
    js_data = json.dumps(all_entries, default = str)
    return HttpResponse(js_data)
           
#Persists loaded tags accross the session.
#Passes a concatonated string split by , since life is hard and ajax has issues
#we just recovert into an array
#Storing plants as well for getLoads()
def persistTags(request):
    request.session['tags'] = request.POST['tags'].split(';;')
    request.session['plants'] = request.POST['plants'].split(';;')
    try:
        request.session['minTime'] = request.POST['minTime']
        request.session['maxTime'] = request.POST['maxTime']
    except:
        request.session['minTime'] = None
        request.session['maxTime'] =  None
    print("Presisted: ", request.session['tags'])
    print("Plants: ", request.session['plants'])
    print('MinTime: ', request.session['minTime'] )
    return HttpResponse()
def sessionTags(request):

    keys = request.session.keys()
    values = {}
    for k in keys:
        values[k] = request.session[k]

    print("Session: ", values)
    js_data = json.dumps(values)
    return HttpResponse(js_data)
#get a specfic column associated with tag/plant from tagInfo.
#I lied I'm just going to get a bunch of them and hard code it :)
def tagGetCol(request):


    plantTagData = eval(f"{request.POST['plant']}TagData")
    tag = request.POST['tag']


    tagIDInfo = plantTagData.select("TAGID_PI", "UNIT_PI", 'engUnits','descriptor').filter(plantTagData.TAG_PI == tag).distinct().collect() 
    tagID = tagIDInfo[0][0]
    tagUnit =tagIDInfo[0][1]
    engUnits = tagIDInfo[0][2]
    descriptor = tagIDInfo[0][3]
    print("tagID:", tagID)
    print("engunits:", engUnits)
    print("desc:", descriptor)
        

    
    values = {'engUnits' : engUnits,
             'descriptor': descriptor}

    js_data = json.dumps(values, default=str)
    return HttpResponse(js_data)
def getData(request,pivot = True,interval = '1m', output = 'spark'):
    tag = request.POST['tag'].split(';;')
    #tag = tag.split(';;')
    # Filters
    minTime = request.POST['minTime']
    maxTime = request.POST['maxTime']
    print('minTime:', minTime)
    print('maxime:', maxTime)
    #PiData utilizes pandas; our original filteredTagData uses spark. Below code has been changed to compensate. Alternatively, you can try converting pandas df to spark df
    rawValues = PIData(tag,minTime, maxTime, 'best', True, pivot,True,interval, datatype = output, appName = 'PIDWFEExtract')
    print('Values got')
    if(type(rawValues) == pd.DataFrame):
        rawValues = rawValues.reset_index() #rawValues has time saved as the row name instead of an actual oclumn to pull so we're  popping it out and adding a regular numeric index
        rawValues = rawValues.astype({'time': 'string'}) #time is currently timezone and str is easier to manipulate
        rawValues = rawValues.dropna() 
        #rawValues.sort_index();
        #WEIRD CASES of PiDate:
        #Parquet has timezone attache to its time
        #WebAPI Doesn't give NaN or null
        #Below, I am covering WebAPI weird returns
        #and also the case in which our time is not in correct format str("YYYY-MM-DD HH-mm-ss" )
        '''badValues = []
        for i in range(0, len(rawValues)):
            if not(isinstance(rawValues.iat[i, 2], (int, float) ) ): #making sure value is acceptable
                badValues.append(i)
            rawValues.iat[i, 0] = rawValues.iat[i, 0][0:19] #go dow index rows and get 3rd column (time)
        #Use .at or .loc of efficiency. Timing sorta bad with large data sets sice iterating is lsow
        rawValues = rawValues.drop(badValues)'''
    #else:
    #    rawValues = rawValues.na.drop()
    #rawValues = rawValues.sort_index()
    return rawValues

def filteredTagDataNew(request):  
    timeInterval = request.POST['timeInterval']
    timeInterval = 'mo' if timeInterval == '1mo' else timeInterval
    rawValues = getData(request, True,timeInterval, 'spark')
    tag = request.POST['tag'].split(';;')
    minTime = request.POST['minTime']
    maxTime = request.POST['maxTime']
    #pandas... is sort of slow
    #Catchihng for webapi pandas return
    if(type(rawValues) == pd.DataFrame):
        rawValues = rawValues.rename_axis(None, axis=1)
        rawValues = rawValues.to_csv()
        return HttpResponse(rawValues)
    else:
        csvPath = os.getcwd() +'/DashboardWebappApp/downloadCSV/'
        csvPath += 'Spark/'  + maxTime[0:10] + '-' + minTime[0:10] + '-' + timeInterval + '+' + "+".join(tag)  + '.csv'
        csvString = rawValues.repartition(1).write.option("header",True).option('timestampFormat', 'yyyy-MM-dd HH:mm:ss').csv(path = csvPath, mode = 'overwrite')
        csvPath = csvPath + '/' + listdir(csvPath)[0]
        file = open(csvPath, 'r')
        return HttpResponse(file.read(), content_type="text/csv", charset="utf-8")
#saves csv then grabs csvstring inside. we do for both but pandas can return a csvstring if need by
#also depreciates fileteredTagDataNew since we wanted a csv string and originally we were converintg from df to list to json to csv anyways soooooooooo
def downloadCSV(request):
    timeInterval = request.POST['timeInterval']
    rawValues = getData(request, True, timeInterval, 'spark')
    tag = request.POST['tag'].split(';;')
    minTime = request.POST['minTime']
    maxTime = request.POST['maxTime']
    
    #BIG WARNING THIS IS WORKING BECAUSE WEBAPI = SMALL AND USE PANDAS FOR THAT
    #IF WE FULLY GO SPARK WE CANNOT COMBINE INTO 1 CSV; BUT SPARK IS FOR BIG STUFF AND WE WOULD SPLIT ANYWAYS SO ITS FINE
    #PANDAS = Assuming we have low data num (can handle multiple tags)
    #SPARK = Assuming we have big data (1 tag at time)
    
    #Rawvalues comes in time | tag | value; need to make it time | valTag1 | valTag2 | valTag3
    csvPath = os.getcwd() +'/DashboardWebappApp/downloadCSV/'
    if(type(rawValues) == pd.DataFrame):
        csvPath += 'Pandas/'  + maxTime[0:10] + '-' + minTime[0:10] + '-' + timeInterval + '+' + "+".join(tag)  + '.csv'
        #rawValues = rawValues.reset_index() #rawValues has time saved as the row name instead of an actual oclumn to pull so we're  popping it out and adding a regular numeric index
        rawValues = rawValues.rename_axis(None, axis=1)
        rawValues.to_csv(csvPath, index=False)
        #processing so it tags on top and values under
    else:
        csvPath += 'Spark/'  + maxTime[0:10] + '-' + minTime[0:10] + '-' + timeInterval + '+' + "+".join(tag)  + '.csv'
        csvString = rawValues.repartition(1).write.option("header",True).option('timestampFormat', 'yyyy-MM-dd HH:mm:ss').csv(path = csvPath, mode = 'overwrite')
        csvPath = csvPath + '/' + listdir(csvPath)[0]
        #Spark handles things fasts with partition, need to break it and put it into 1 file and also it saves as folder :))))))
    # Open the file for reading content
    file = open(csvPath, 'r')
    response = HttpResponse(file.read(), content_type="text/csv", charset="utf-8")
    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(csvPath)
    return response



def filteredTagData(request):
	plantTagData = eval(f"{request.POST['plant']}TagData")
	plantData = eval(f"{request.POST['plant']}Data")
	tag = request.POST['tag']

	# Filters
	minTime = request.POST['minTime']
	maxTime = request.POST['maxTime']
	print('minTime:', minTime)
	print('maxime:', maxTime)
	tagID_and_unit = plantTagData.select("TAGID_PI", "UNIT_PI").filter(plantTagData.TAG_PI == tag).distinct().collect() 
	tagID = tagID_and_unit[0][0]
	tagUnit = tagID_and_unit[0][1]
	
	print("tagID:", tagID)
    
	rawValues = plantData[f'U{(tagID // 1_000_000) % 100}C{(tagID // 10_000) % 100}'].filter(f"tag = {tagID}").filter((F.col("time") >= minTime) & (F.col("time") <= maxTime)).orderBy(F.col("time").asc())
	rawValues = rawValues.na.drop()

    
	values = dict(map(lambda x: (x['time'].isoformat(), float(x['value'])), rawValues.collect()))

	js_data = json.dumps(values, default=str)
	return HttpResponse(js_data)

# Retrieve load values for each unit of each plant
#I feel like i want to get rid of this function or rename it. - alvin 7/12
def getLoads(request):
    returnData = {}
    tags = request.session.get('tags')
    plants = request.session.get('plants')
    try:
        if(request.session['minTime'] == None or request.session['minTime'] == None):
            raise "wow"
        else:
            returnData['times'] = [request.session['minTime'],  request.session['maxTime'] ]
    except:
        print('no times')
        returnData['times']  = [None, None]
    print("Session Tags: ", tags)
    print("Session Plants: ", plants)

    try:
        for tag in tags:
            plantTagData = eval(f"{plants[tags.index(tag)]}TagData")
            tagName, engUnits, descriptor = plantTagData.select("TAG_PI", "engunits", "descriptor").filter(plantTagData.TAG_PI == tag).distinct().collect()[0]
            returnData[tagName] = [tag, plants[tags.index(tag)], engUnits, descriptor]

    except NameError:
        print(NameError)
    finally:
        print("getLoads Data: ", returnData)
        js_data = json.dumps(returnData)
        return HttpResponse(js_data)	



    #Search joins multiple tables by search parameters provided
def advancedSearch(request):
    #In order of TagName, tag ID Eng Units attribute description.
    print(request.POST['searchParameters'].split(";;"))
    searchParameters = request.POST['searchParameters'].split(";;")
    #popping out of list so my select statement isn't the ugliest thing in the world
    tagSearch = searchParameters.pop(0).lower()
    #tagSearch = tagSearch.replace('.','\.')
    tagSearch = '*' + tagSearch + '*' 
    tagSearch = tagSearch.replace('*', '%')
    print(tagSearch)
    #idSearch = searchParameters.pop(0).lower()
    engSearch = searchParameters.pop(0).lower()
    engSearch = '*' + engSearch + '*' 
    engSearch = engSearch.replace('*', '%')
    print(engSearch)
    descSearch = searchParameters.pop(0).lower()
    descSearch = '*' + descSearch + '*' 
    descSearch = descSearch.replace('*', '%')
    print(descSearch)
    
    require = request.POST['require']
    
    #Above 4 are from same query
    #requestedAttributes = eval('attributes')
    #requestedAttributes = requestedAttributes.sort_values(by=['Element'])
    attSearch = searchParameters.pop(0).lower()
    join = '&' if  require == 'true' else '|' 
    filter = '(lower(plantTagData.TAG_PI).like(tagSearch)) '  + join + '( (lower(plantTagData.engunits).like(engSearch)) | (plantTagData.engunits).isNull() )' + join + ' ( (lower(plantTagData.descriptor).like(descSearch) | (plantTagData.descriptor).isNull()) )'
    print(filter)
    #Each query is unique so we must split amongst
    #Tag ID and ENG
    data = []
    #Thinking about making tagData a global in app.py... surely i shouldnt... - alvin
    #py spark why
    for plant in ['brown', 'canerun', 'ghent',  'millcreek', 'trimble']:
        plantTagData = eval(f"{plant}TagData")
        t1 = plantTagData.select("TAG_PI", "TAGID_PI", "engunits", "descriptor").filter(eval(filter)).distinct().orderBy(plantTagData.TAG_PI.asc()).collect()
        
        if t1 != []:
            data = data + t1
    
    
    
    #requestedAttributes.Element.str.contains(f"{attSearch}", case=False) | 
    #requestedAttributes.pitag.str.contains(f"{searchValue}", case=False) |
    #Pandas why
    #matchedAttributes = requestedAttributes[requestedAttributes.AttributeName.str.contains(f"{attSearch}", case=False) |  requestedAttributes.att_description.str.contains(f"{descSearch}", case=False)]
    
    #data = data.toPandas()

    
    values = {}
    values = dict(map(lambda x: (x[0], [x[0], x[1], x[2], x[3]]), data)) 
    js_data = json.dumps(values, default=str)
    return HttpResponse(js_data)
