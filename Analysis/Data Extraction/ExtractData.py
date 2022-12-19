from pExtractData import *
from sExtractData import *
from datetime import datetime, timedelta
from pytz import timezone, all_timezones
#UDF needs spark session to start unfortunately
#Did not want to start spark session inbeginning but woe as me

#okay so to retierate:
#WEB API GIVES EST OR EDT DEPENDING ON SEASON
#PDW GIVES EST ONLY
#BOTH HAVE ADJUSTED FOR SIAD
#INPUT IS WATCH TIME, OUTPUT IS EST ALWAYS

def findParquetFiles(tagIDs):
    parquetFiles = {}
    if type(tagIDs) != list:
        tagIDs = [tagIDs]
    for tag in tagIDs:

        plants = {
        1:'brown',
        2:'canerun',
        3:'ghent',
        4:'millcreek',
        5:'trimble',
        }
        t = int(tag/10000)
        c = (str(int(t%100)) if int(t%100) >= 10 else '0' + str(int(t%100)))
        u = int(int(t/100)%100)
        p = plants[int(int(t/10000)%10)]



        newFile = f'/u01/JupyterFolder/Production/Parquet/{p}_U{u}_Core_{c}.parquet'
        if (newFile in parquetFiles.keys()):
            parquetFiles[newFile].append(tag)
        else:
            parquetFiles[newFile] = [tag]
    return parquetFiles


#Input is string time, and then we convert to data later

def ExtractPIData(tags,start,end, method = 'best',returnNames = False, pivot = False,interpolated=True,interval='1m',datatype = 'pandas', appName = "Extract_Alvin"):
    
    start =datetime.strptime(start, '%Y-%m-%d %H:%M:%S')#.astimezone(timezone('EST')).strftime("%Y-%m-%d %H:%M:%S%z")
    end =datetime.strptime(end, '%Y-%m-%d %H:%M:%S')#.astimezone(timezone('EST')).strftime("%Y-%m-%d %H:%M:%S%z")
    
    #method inputs: ['best', webAPI, parquet, interpArchive, interp]
    method = method.lower() #I've been griefed by webAPI vs WebAPI too many times...
    datatype = datatype.lower() #Just in case
    ids = []
    names = []
    #If you enter a mix of names and tags I will personally come and poke you - Alvin
    
    
    #Checking what kind of data input we have
    #If tagname, we have to convert into tagID for Data Analyrtics Processing
    #If TagID, we have to convert to tagName for WebAPI
    if type(tags) == list:
        try:
            int(tags[0])
            ids = tags
        except:
            names = tags
    else:
        try:
            int(tags)
            ids = [tags]
        except:
            names = [tags]
    print(tags)
    print(ids)
    print(names)
    names = [n.lower() for n in names]
    
    
    #Table's TimeRanges      
    #I use pands since i'm lazy and don't wantto starta a spark session
    #
    sources = {}
    if method == 'best':
        #Low enough data size?
        rowSum=(end-start).total_seconds()/60
        rowSum = rowSum / (60*24*30) if interval == 'mo'  else rowSum
        rowSum = rowSum / (60*24*7) if interval == '1w' else rowSum
        rowSum = rowSum / (60*24) if interval == '1d' else rowSum #get first hour and 
        rowSum = rowSum / 60 if interval == '1h' else rowSum #Get first minute of every hour
        if (rowSum<300000):
            sources = {'webapi': [start,end]}
        else: #long long logic, using time ranges
            timeRanges = pExtractPostgres("SELECT * FROM \"PI\".\"TimeRanges\"")
            for row in timeRanges.values:
                row[1] = row[1].to_pydatetime()
                row[2] = row[2].to_pydatetime()
                range = []
                if (row[1] <= start and start <= row[2]): #Starts in range
                    range.append(start)
                    if (row[1] <= end and end <= row[2]): #ends in range
                        range.append(end) #End result is START - END as given
                    else:
                        range.append(row[2]) #End result is START - TABLEEND
                elif (row[1] <= end and end <= row[2]): #If not starting, see if we end in it. if so, range is tablestart - endgiven
                    range = [row[1], end] #End Result is TABLESTART - END 
                elif (start <= row[1] and row[2] <= end): #If not, check if range inside
                    range = [row[1], row[2]] #End Result is TABLESTART - TABLEEND
                if range != []:
                    sources[row[0].lower()] = range
            #If for some reason we are not in any range and didn't add anything... some how...
            if len(sources) == 0:
                sources = {'webapi': [start,end]}
                    
    else:
        ['best', 'webapi', 'parquet', 'interparchive', 'interp'].index(method)
        #Intentionally breaking it, will trhow error if method is not in our chosen few.
        #If you wanted to properlly do it, shoud be just 
        #if method in [] else throw exception
        sources = {method: [start, end]}
    print(sources)
    
    
    
    #parsing TagName => TagID and vice versa
    #The necessity of the parsing depends on if we have correct formats
    #WebAPI needs tagNames
    #All other methos need ID's
    #If one is without other, grab
    #Also need pitags if our output is different than what we get from functions
    pitags = "placeholder :)"
    if('webapi' in sources.keys() and len(names) == 0) or (len(names) != 0 and (len(set(sources.keys()).intersection(set(['parquet', 'interparchive', 'interp']))) > 0)) or ('webapi' in sources and returnNames == False) or ('webapi' not in sources and returnNames == True):
        print('accessing pitag table')
        if len(names) == 0: #grab names
            pitags = pExtractPostgres(f"SELECT lower(\"TAG_PI\") as \"TAG_PI\" ,\"TAGID_PI\" FROM \"PI\".\"PITAG\" WHERE \"TAGID_PI\" in {ids}".replace('[', '(').replace(']',')'))
            names = pitags["TAG_PI"].values
        else: #grab ids
            pitags= pExtractPostgres(f"SELECT lower(\"TAG_PI\") as \"TAG_PI\",\"TAGID_PI\" FROM \"PI\".\"PITAG\" WHERE lower(\"TAG_PI\") in {names}".replace('[', '(').replace(']',')'))
            ids = [int(x) for x in pitags["TAGID_PI"].values]
            #Pandas gives numpy.int64, and pyspark gets angry when we use that
            
            
            
            
    out = 'placeholder so I can output it later, something about scope'
    print('data start')
    #Datagrab cquence
    #Parquet needs timezone added to function correctly.
    if datatype == 'pandas':
        out = pd.DataFrame()
        out['tag'] = []
        out['time'] = []
        out['value'] = []
        if 'webapi' in sources:
            out = pd.concat([out,pDriverWebAPI(names, sources['webapi'][0], sources['webapi'][1], interpolated, interval)])
        if 'parquet' in sources:
            out = pd.concat([out,pDriverParquet(findParquetFiles(ids),sources['parquet'][0].astimezone(timezone('EST')).strftime("%Y-%m-%d %H:%M:%S%z"), sources['parquet'][1].astimezone(timezone('EST')).strftime("%Y-%m-%d %H:%M:%S%z"))])
        if 'interparchive' in sources:
            out = pd.concat([out,pExtractPostgres(f'SELECT * FROM \"PI\".\"PIInterpArchive\" WHERE \"tag\" in {(ids)} AND \"time\" BETWEEN \'{sources["interparchive"][0]}\' AND \'{sources["interparchive"][1]}\''.replace('[', '(').replace(']',')'))])
        if 'interp' in sources:
            out = pd.concat([out,pExtractPostgres(f'SELECT * FROM \"PI\".\"PIInterp\" WHERE \"tag\" in {(ids)} AND \"time\" BETWEEN \'{sources["interp"][0]}\' AND \'{sources["interp"][1]}\''.replace('[', '(').replace(']',')'))])
            
            
    elif datatype== 'spark':
        out = spark.createDataFrame(data = spark.sparkContext.emptyRDD(), schema = StructType([StructField("tag", StringType(), False),
                                                                                                StructField('time', TimestampType(), False),
                                                                                                StructField('value', DecimalType(), True)
    ]))
        if 'webapi' in sources:
            out = out.union(sDriverWebAPI(names, sources['webapi'][0], sources['webapi'][1], interpolated, interval))
            
        if 'parquet' in sources:
            out = out.union(sDriverParquet(findParquetFiles(ids),sources['parquet'][0].astimezone(timezone('EST')).strftime("%Y-%m-%d %H:%M:%S%z"), sources['parquet'][1].astimezone(timezone('EST')).strftime("%Y-%m-%d %H:%M:%S%z")))
        if 'interparchive' in sources:
            out = out.union(sExtractPostgres(f'SELECT * FROM \"PI\".\"PIInterpArchive\" WHERE \"tag\" in {ids} AND \"time\" BETWEEN \'{sources["interparchive"][0]}\' AND \'{sources["interparchive"][1]}\''.replace('[', '(').replace(']',')')))
        if 'interp' in sources:
            out = out.union(sExtractPostgres(f'SELECT * FROM \"PI\".\"PIInterp\" WHERE \"tag\" in {ids} AND \"time\" BETWEEN \'{sources["interp"][0]}\' AND \'{sources["interp"][1]}\''.replace('[', '(').replace(']',')')))
            
    else:
        return "You made me do a lot of work for nothing"
    print('data finished')
        
    #adding tag id's or tag names whatever is needed
    #Web Api only occurs alone and its only one that gives tagnames, so convert to ID 
    dict = {}
    if ('webapi' in sources and returnNames == False) or ('webapi' not in sources and returnNames == True):
        #https://stackoverflow.com/questions/26716616/convert-a-pandas-dataframe-to-a-dictionary 
        #wooo
        print('converting names and ids')
        if returnNames == True:
            dict = pitags.set_index("TAGID_PI").T.to_dict('list')
        else:
            dict = pitags.set_index("TAG_PI").T.to_dict('list')
        print(dict)
        if datatype=='pandas':  
            out['tag'] = out['tag'].apply(lambda x: dict[x][0])
        elif datatype =='spark':
            fun = 'fun'
            if returnNames == True:
                fun = udf(lambda x: dict[int(x)][0], StringType())
            else:
                fun = udf(lambda x: dict[x][0], IntegerType())
            out = out.withColumn('tag', fun('tag'))
    #pivot
    if pivot == True:
        print('pivoting data')
        if datatype == 'spark':
            #print("before removing tag/time nulls", df.count())
            out=out.where(out.time.isNotNull() & out.tag.isNotNull())
            #print("after removing tag/time nulls", df.count())
            out=out.dropDuplicates(['tag', 'time'])
            #print("after removing duplicates", df.count())
            out = out.groupBy('time').pivot('tag').sum('value') #if the previous line for removing duplicates works as it's supposed to then this should accurately pivot the data...
            # if you want, you can check that the count of the pre-pivoted data is equal to -> (len(query_result.columns)-1)*query_result.count()
            out=out.sort('time')
        elif datatype =='pandas':
            out=out.dropna(subset=['tag', 'time'])
            out=out.drop_duplicates(subset=['tag', 'time'], keep='last')
            #df['value']=df['value'].apply(pd.to_numeric)
            
            out = out.pivot(index='time', columns='tag',values = 'value')
            out = out.sort_values(by=['time'])
    else:
        print('not pivoting')    
        if datatype =='spark':
            out= out.sort('tag','time')
        elif datatype =='pandas':
            out=out.set_index('time')
            out=out.sort_index()
    
    #interval
    #Maybe change all the datatype == 'string' to check type directly in case.
    try:
        if (type(out) == pyspark.sql.dataframe.DataFrame and interval != '1m') and 'webapi' not in sources.keys():
            print('filtering time')
            out = out.filter("DAY(time) == 1 and HOUR(time) == 0 and MINUTE(time) == 0") if interval == 'mo'  else out
            out = out.filter("DAY(time) % 7 == 0 and HOUR(time) == 0 and MINUTE(time) == 0") if interval == '1w' else out
            out = out.filter("HOUR(time) == 0 and MINUTE(time) == 0") if interval == '1d' else out #get first hour and 
            out = out.filter("MINUTE(time) == 0") if interval == '1h' else out #Get first minute of every hour
        if (type(out) == pd.core.frame.DataFrame and interval != '1m') and 'webapi' not in sources.keys():
            print('filtering time')
            out = out[np.logical_and(np.logical_and(out.index.day == 1, out.index.minute == 0), out.index.hour == 0)] if interval == 'mo'  else out
            out = out[np.logical_and(np.logical_and(out.index.day % 7 == 0, out.index.minute == 0), out.index.hour == 0)] if interval == '1w' else out
            out = out[np.logical_and(out.index.minute == 0, out.index.hour == 0)] if interval == '1d' else out
            out = out[out.index.minute == 0] if interval == '1h' else out
    except:
        print('normally i would print out an error but it would seem tings are broken at the filtering stage')
    
    
    return out