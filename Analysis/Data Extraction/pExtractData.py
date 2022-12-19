#webAPI
from requests.auth import HTTPBasicAuth
import requests
import json
from datetime import datetime, timedelta
#PostGres
from sqlalchemy import create_engine

#Parquet
from multiprocessing import Process, Queue
from multiprocessing import Pool, TimeoutError

import pandas as pd
from pytz import timezone, all_timezones
import urllib3
urllib3.disable_warnings()

CONFIG = {'PIWEBAPI_URL' : '',
            'SERVER' : '',
            'SECURITY_METHOD' : 'basic',
            'USER' : '',
            'PASSW' : '', #
            'VERIFY_SSL' : False}
def call_security_method(security_method, user_name, user_password):
    
    if security_method.lower() == 'basic':
        security_auth = HTTPBasicAuth(user_name, user_password)
        
    return security_auth
def getRequest(urlString): 
    security_auth = call_security_method(CONFIG['SECURITY_METHOD'], CONFIG['USER'], CONFIG['PASSW'])
    response = requests.get(urlString, auth=security_auth, verify=CONFIG['VERIFY_SSL'])
    return response



#DATES COME IN WATCH TIME (EST OR DST)
#DATE COME OUT IN SERVER TIME (EST)
def pExtractParquet(file, tags, start, end, q = None):
    
    pandata = pd.read_parquet(file)
    pandata = pandata[pandata['tag'].isin(tags)]
    pandata['time'] = pandata['time'].dt.tz_localize('UTC')
    pandata['time'] = pandata['time'].dt.tz_convert('EST')
    pandata = pandata[(pandata['time'] >= start) & (pandata['time'] <= end) & (pandata['tag'].isin(tags))]
    if q == None:
        return pandata
    else:
        q.put(pandata)

def pDriverParquet(parquetFiles, start, end):
    
    df = pd.DataFrame()
    df['tag'] = []
    df['time'] = []
    df['value'] = []
    queue = Queue()


    processes = [Process(target=pExtractParquet, args=(file, parquetFiles[file],start,end,queue,)) for file in parquetFiles]
    for p in processes:
        p.start()
    for p in processes:
        df=pd.concat([df,queue.get()])
        p.join()
        p.close()
    queue.close()
    return df

def pExtractPostgres(query):
    alchemyEngine = create_engine('postgresql://:@localhost:5432/GENERATION')
    dbConnection = alchemyEngine.connect()
    pandata = pd.read_sql(query, dbConnection)
    return pandata

#WEBAPI FUNCTIONS

def pExtractWebAPI(tagID, start, end,  interp = True, interval = '1m', q = None):
    CONFIG = {'PIWEBAPI_URL' : '',
            'SERVER' : '',
            'SECURITY_METHOD' : 'basic',
            'USER' : '',
            'PASSW' : '', #
            'VERIFY_SSL' : False}
    rowSum=int((end-start).total_seconds()/60)
    loopData = pd.DataFrame()
    #print('rowSum = ',rowSum)
    increment = 120000 
    for i in range(0, rowSum, increment):
        data = pd.DataFrame()
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
                    #print(dataLink)
                    responseDataString = getRequest(dataLink)
                    if responseDataString.status_code == 200:

                        dataString = responseDataString.text
                        
                        dataSubString = dataString[dataString.index('['):dataString.index(']')+1]
                        try:
                            dataList = json.loads(dataSubString)
                        except: #when you get an erro return, usualy its when oy
                            df = pd.DataFrame()
                            return df
                        df = pd.DataFrame(dataList)
                        df['tag'] = tagID
                        data = pd.DataFrame()
                        data['tag'] = df['tag']
                        data['time'] = df['Timestamp']
                        #data1[pd.to_numeric(data1['millcreek.u1.1c3239.daca.pv'], errors ='coerce').isnull()]
                        try:
                            data['value'] = df.apply(lambda x: x['Value'] if x['Good'] == True else None, axis=1)
                            data['value'] = data.apply(lambda x: int(x['value']['Value']) if x['value']['Value'] != None else None, axis = 1)
                        except:
                            data['value'] = df['Value']
                        data['time'] = pd.to_datetime(data['time'], format = '%Y-%m-%d %H:%M:%S', errors ='coerce')
                        data['time'] = data['time'].dt.tz_convert('Etc/GMT+5')#EST without Daylight Saving
                        data['value'] = pd.to_numeric(data['value'], errors ='coerce')
                        #data['time'] = data['time'].dt.tz_localize(None) #Remove timezone from column
                    else:
                        if q == None:
                            return f"API Call Failed at Data String Level. Status code {responseDataString.status_code}"
                        else:
                            q.put( f"API Call Failed at Data String Level. Status code {responseDataString.status_code}")
                else:
                    if q == None:
                        return "Tag Not Found " + str(tagID)
                    else:
                        q.put("Tag Not Found")
            else:
                if q == None:
                    return f"API Call Failed at Meta Data Level. Status code {responseMetaData.status_code}"
                else:
                     q.put(f"API Call Failed at Meta Data Level. Status code {responseMetaData.status_code}")
        else:
            if q == None:
                return f"API Call Failed at Element Web ID Level. Status code {responseWebID.status_code}"
            else:
                q.put(f"API Call Failed at Element Web ID Level. Status code {responseWebID.status_code}")
        loopData = pd.concat([loopData, data])
    if q == None:
        return loopData
    else:
        q.put(loopData)
def erroring(error):
    print(f'Pool got an error: {error}')
    return pd.DataFrame()
def pDriverWebAPI(tagIDs, start, end, interp = True, interval = '1m', workers = 6):
    try:
        df = pd.DataFrame()
        df['tag'] = []
        df['time'] = []
        df['value'] = []
        if type(tagIDs) != list:
            print('try inputting a list []')
            tagIDs = [tagIDs]
        #for tag in tagIDs:
        #    df=pd.concat([df,pExtractWebAPI(tag,start,end,interp, interval)])
        '''
        queue = Queue()
        processes = [Process(target=pExtractWebAPI, args=(id,start,end,interp, interval, queue,)) for id in tagIDs]
        for p in processes:
            p.start()
        for p in processes:
            try:
                pos = queue.get()
                #print('got')
                if pos.equals(pd.DataFrame):
                    for stop in processes:
                        stop.close()
                        queue.close()
                    print('dies of cringe')
                    return pd.DataFrame()
                df=pd.concat([df,pos])
                p.join()
            except TypeError:
                print('SOmething broke', TypeError)
            finally:
                p.close()
        queue.close()
        '''
        arguments = [[id, start,end,interp,interval,] for id in tagIDs]
        with Pool(processes = workers) as pool:
            result = pool.starmap_async(pExtractWebAPI, arguments, error_callback=erroring)
            df = result.get()
            try:
                df = pd.concat(df)
            except Exception as e:
                print('Concat',e,df)
        return df
    except Exception as e:
        print('DriverWebAPI:', e)
        return  pd.DataFrame()
    
