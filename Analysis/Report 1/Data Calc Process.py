import sys
import urllib3
import math
import numpy as np
urllib3.disable_warnings()
sys.path.insert(1,'/u01/JupyterFolder/Production/Analysis/DataExtraction')
from pExtractData import *
from plant_constants import PLANT_CONSTANTS as constants
alchemyEngine = create_engine('postgresql://postgres@localhost:5432/GENERATION')
dbConnection = alchemyEngine.connect()

def pressure_saturation(temperature:float) -> float:
    return 0.00000002392*(temperature**4) - 0.000003952*(temperature**3) + 0.0005051*(temperature**2) - 0.01995*(temperature) + 0.4416

def hei_correction(temperature:float) -> float:
    return 0.000000661 * temperature**3 - 0.000240000 * temperature**2 + 0.030100000 * temperature - 0.169

def call_security_method(security_method, user_name, user_password):
    if security_method.lower() == 'basic':
        security_auth = HTTPBasicAuth(user_name, user_password)

    return security_auth

def getRequest(urlString): 
    security_auth = call_security_method(CONFIG['SECURITY_METHOD'], CONFIG['USER'], CONFIG['PASSW'])
    response = requests.get(urlString, auth=security_auth, verify=CONFIG['VERIFY_SSL'])
    return response

def postRequest(urlString, body):
    security_auth = call_security_method(CONFIG['SECURITY_METHOD'], CONFIG['USER'], CONFIG['PASSW'])
    response = requests.post(urlString, json = body, auth=security_auth, verify=CONFIG['VERIFY_SSL'])
    return response
def savePiValues(TagID,valueList,timeList):
    CONFIG = {'PIWEBAPI_URL' : '',
                'SERVER' : '',
                'SECURITY_METHOD' : 'basic',
                'USER' : '',
                'PASSW' : '',
                'VERIFY_SSL' : False}
    getDatabaseQuery = f"{CONFIG['PIWEBAPI_URL']}/dataservers?path=\\PIServers[{CONFIG['SERVER']}]"
    responseWebID = getRequest(getDatabaseQuery)
    if responseWebID.status_code == 200:
            database = json.loads(responseWebID.text)
            WebID = database['WebId']
            metaDataURL = f"{CONFIG['PIWEBAPI_URL']}/dataservers/{WebID}/points?nameFilter={TagID}"
            responseMetaData = getRequest(metaDataURL)
            if responseMetaData.status_code == 200:
                tagMetaData = json.loads(responseMetaData.text)
                TagWebID = tagMetaData['Items'][0]['WebId']
                postUrl = tagMetaData['Items'][0]['Links']['Value']
              
                for x in range(0,len(valueList)):
                    body = {"Timestamp": timeList[x],
                        "UnitsAbbreviation": "",
                        "Good": "true",
                        "Questionable": "false",
                        "Value": valueList[x]}
                    responsePost = postRequest(postUrl, body)
    return responsePost



def TagToVar(tag):
    plant = {
        'Brown':'BR',
        'Ghent':'GH',
        'MillCreek':'MC',
        'Trimble':'TC',
        
    }
    tag = tag.split('.') #Ghent.u1.xxxx
    #-> Ghent = GH
    return tag[2] +'-' + plant[tag[0]] +tag[1][1:]

def shortToLongPU(plantUnit):
        plant = {
            'BR':'Brown',
            'GH':'Ghent',
            'MC':'MillCreek',
            'TC':'Trimble',

        }
        return plant[plantUnit[:2]] + ".U" + plantUnit[2:]


def latestShift(shiftHour = 6) -> (pd.Timestamp, pd.Timestamp): #This returns latest shift in local time, not adjusted for est for PDW
    now = datetime.utcnow()-timedelta(hours=5)
    now2 = datetime.now()
    est = now.hour==now2.hour
    #===========Manual
    #now = datetime.strptime('11/9/22 19:00:00', '%m/%d/%y %H:%M:%S')
    #est = True

    #Find Shift Changes
    AM = datetime(now.year, now.month, now.day, int(shiftHour),1)
    PM=AM+timedelta(hours=12)
    if AM>now:
        shiftEnd = AM-timedelta(hours=12)
    elif PM>now:
        shiftEnd = AM
    else:
        shiftEnd= PM 
    shiftStart=shiftEnd-timedelta(hours=12)
    shiftEnd = shiftEnd-timedelta(minutes=1)
    #dst we shift back 1 hour. Need to keep local time for PI
    #But EST of PDW
    #estStart = shiftStart 
    #estEnd = shiftEnd 
    #if(not est):
    #    estStart = shiftStart  -timedelta(hours=1)
    #    estEnd = shiftEnd -timedelta(hours=1)
    return shiftStart,shiftEnd#,estStart,estEnd

def dcoProcess(units:list, piStart:pd.Timestamp, piEnd:pd.Timestamp,inputParameters:list = [], audit = False) -> (pd.DataFrame,dict):
    #pdw time
    pdwStart = piStart
    pdwEnd = piEnd
    est = (datetime.utcnow()-timedelta(hours=5)).hour == datetime.now().hour
    if not est:
        pdwStart = pdwStart -timedelta(hours=1)
        pdwEnd = pdwEnd - -timedelta(hours=1)

    audits = {}
    if (inputParameters==[]):
        inputParameters = ['Main Steam Temperature', 'Main Steam Pressure', 'Hot Reheat Temp', 
                   'Aux Power', 'Boiler/Economizer O2', 'Reheat Spray Flows','Superheat Spray Flows', 
                   'Feedwater Flow', 'Condenser Pressure', 'Condenser Pressure LP', 'Condenser Pressure HP', 
                   'Main Steam Flow', 'Heat Rate', 'Condenser Inlet Temp']
    data1 = pd.DataFrame()
    #make it so we get unit 0 as well
    plants = set([p[0:2] for p in units])
    bonk = "\'" + "%%\',\'".join(plants) + "%%\'"
    
    TagQuery = f"""
    SELECT 
        "Parameter"
        ,"PlantUnit"
        ,"ActualOrTarget"
        ,"PiTag"
        ,"Notes"
        ,"TAGID"
    FROM "PI"."DCO_Parameters" 
    WHERE "PlantUnit" like any (array[{bonk}])
    """
    parameters = pExtractPostgres(TagQuery)

    TagQuery = f"""
    SELECT 
        "TAGID"
        ,"PiTag"
    FROM "PI"."DCO_OutputParameters" 
    """
    outputParameters = pExtractPostgres(TagQuery)

    returnData = pd.DataFrame()
    for unit in units:
        unitData = pd.DataFrame()
        if audit:
            #Logging
            save = {}
            save['START'] = [pdwStart]
            save['END'] = [pdwEnd]
            save['PLANT'] = [unit]
            insert = pd.DataFrame.from_dict(save)
            insert.to_sql(schema= 'PI', name='DCO_Audit', con=alchemyEngine, if_exists='append', index=False)
            auditQuery = f"""
            SELECT 
                "ID" 
            FROM "PI"."DCO_Audit" 
            WHERE "START" = '{datetime.strftime(pdwStart, '%Y%m%d %H%M%S')}' 
                AND "END" = '{datetime.strftime(pdwEnd, '%Y%m%d %H%M%S')}' 
                AND "PLANT" = '{unit}' 
            ORDER BY "ID" DESC
            """
            auditID = pExtractPostgres(auditQuery).iloc[0][0]
            audits[unit]=auditID
        print('start unit', unit)
        #Data Grab
        for parameter in inputParameters:
            tagsOfInterest = []
            tagsOfInterest = parameters[(parameters.Parameter == parameter)]
            tagsOfInterest = tagsOfInterest[tagsOfInterest.PlantUnit.str.contains(unit)]
            tagsOfInterest["Parameter"] = tagsOfInterest["Parameter"] + '-' + tagsOfInterest["ActualOrTarget"]+ '-' + tagsOfInterest["PlantUnit"]
            if not tagsOfInterest.empty:
                d = pDriverWebAPI(tagsOfInterest["PiTag"].tolist(),piStart,piEnd)
                d.reset_index(inplace=True)
                d = pd.merge(d, tagsOfInterest, left_on='tag', right_on='PiTag').drop(columns=['tag', 'ActualOrTarget','PiTag','TAGID'])
                unitData = pd.concat([unitData, d])
                test1 = tagsOfInterest

        test = unitData
        #PRetty sure all data uess this one
        ggTags = parameters[(parameters.Parameter == 'Gross Generation')&(parameters.ActualOrTarget == 'Actual')]
        ggTags = ggTags[ggTags.PlantUnit.str.contains(unit)]
        ggTags["Parameter"] = ggTags["Parameter"] + '-' + ggTags["ActualOrTarget"]+ '-' + ggTags["PlantUnit"]
        d = pDriverWebAPI(ggTags['PiTag'].tolist(),piStart,piEnd)
        d.reset_index(inplace=True)
        d = pd.merge(d, ggTags, left_on='tag', right_on='PiTag').drop(columns=['tag', 'ActualOrTarget','PiTag','TAGID'])
        unitData = pd.concat([unitData, d])
        #tags that are unit 0, so we just want to reference by plant.
        plantTags = parameters[parameters.Parameter == 'Cost of Coal - High Sulfur']
        plantTags = pd.concat([plantTags,  parameters[parameters.Parameter == 'Cost of Coal - PRB']])
        plantTags = pd.concat([plantTags,  parameters[parameters.Parameter == 'Barometric Pressure']])
        plantTags["Parameter"] = plantTags["Parameter"] + '-' + plantTags["ActualOrTarget"]+ '-' + plantTags["PlantUnit"].str[:2]
        d = pDriverWebAPI(plantTags['PiTag'].tolist(),piStart,piEnd)
        d.reset_index(inplace=True)
        d = pd.merge(d, plantTags, left_on='tag', right_on='PiTag').drop(columns=['tag', 'ActualOrTarget','PiTag','TAGID'])
        unitData = pd.concat([unitData, d])
        rawData = d.copy()
        #Sometimes we get bad values from pi and we just want to ignore
        unitData['value'] = pd.to_numeric(unitData['value'].astype(str), errors='coerce', downcast = 'float')

        #Some AUX Power Brown Tags are in KW when we edo math in MW so we divide 1000
        unitData['value'] = unitData.apply(lambda x: x['value']/1000 if '/1000' in str(x['Notes']) else x['value'], axis = 1)
        print(f"end unit {unit}")




        means = unitData[unitData.Notes.str.lower().str.contains('avg', na=False)].groupby(['time', 'Parameter'])['value'].mean().reset_index()
        sums =  unitData[unitData.Notes.str.lower().str.contains('sum',na=False)].groupby(['time', 'Parameter'])['value'].sum().reset_index()
        neutrals = unitData[unitData.Notes.str.lower().str.contains('avg|sum', na=False) == False].drop(columns=['PlantUnit', 'Notes', 'index'])
        unitData = pd.concat([means, sums, neutrals])



        unitData = unitData.pivot(index='time', columns='Parameter')['value']
        #TC2 uses a mix ofHS and PB, and evryone else uses HS, so we just overwritethe value forfun
        if unit == 'TC2':
            unitData['Cost of Coal - High Sulfur-Actual-TC'] = unitData['Cost of Coal - High Sulfur-Actual-TC']*0.65 + unitData['Cost of Coal - PRB-Actual-TC'] * 0.35
        try:
            #https://stackoverflow.com/questions/19125091/pandas-merge-how-to-avoid-duplicating-columns
            data1 = pd.merge(data1,unitData,left_on='time',right_on='time', suffixes=('', '_y')).sort_values('time')
            data1.drop([x for x in data1 if x.endswith('_y')], axis=1, inplace=True)
        except:
            data1 = unitData
        if(audit):
            auditQuery = f"UPDATE \"PI\".\"DCO_Audit\" SET \"DATA\" = True WHERE \"ID\" = {audits[unit]}"
            dbConnection.execute(auditQuery)
        

    





#def dcoCalc(data:pd.DataFrame(), inputParameters:list, audits:dict = {}) -> (pd.DataFrame(),dict):
    #uh maybe smush this into dcoData
    #units = [c.split('-')[2] for c in data.columns if 'Gross Generation' in c]
    #print(units)
    data = data1.copy()
    
    # EDR 11/23/22: Added in fix for miscalculated HeatRateActual
    #--------------------------------------------------------------
    data[f'Heat Rate-Actual-{unit}'] = (
        (constants[unit]['GTHRa2'] * data[f'Gross Generation-Actual-{unit}']**2 + 
         constants[unit]['GTHRa1'] * data[f'Gross Generation-Actual-{unit}'] + 
         constants[unit]['GTHRa0']) * 1000) / data[f'Gross Generation-Actual-{unit}']
    #--------------------------------------------------------------
    
    for unit in units:
        #GUHR

        if'Heat Rate' in inputParameters:
            data['GUHR-' + unit] = data['Heat Rate-Actual-' + unit]/ (constants[unit]['boilerEfficiency'] / 100)


        if 'Aux Power' in inputParameters:
            data['Aux_Target-' + unit] = constants[unit]['AUXa']*(data['Gross Generation-Actual-' + unit]**3) + constants[unit]['AUXb']*(data['Gross Generation-Actual-' + unit]**2) + constants[unit]['AUXc']*data['Gross Generation-Actual-' + unit] + constants[unit]['AUXd']
            data[f'AUX_Target-{unit}'] = data[f'Aux_Target-{unit}']
            data['GTHR-Target-' + unit] = (data['Heat Rate-Actual-' + unit]*data['Gross Generation-Actual-' + unit]) / ( data['Gross Generation-Actual-' + unit]+ (data['Aux Power-Actual-' + unit] - data['Aux_Target-' + unit] ))
            data['Aux_ChangeHeatInput-' + unit] = ((data['Heat Rate-Actual-' + unit] - data['GTHR-Target-' + unit]) / (constants[unit]['boilerEfficiency']/100))   *data['Gross Generation-Actual-' + unit]*1000 /1000000/60
            data['Aux_CostOfDeviation-' + unit] = data['Aux_ChangeHeatInput-' + unit] *data['Cost of Coal - High Sulfur-Actual-'+unit[:2]] #Coal Cost
            data['Aux_GUHR_Impact-' + unit] = data['Aux_ChangeHeatInput-' + unit]*1000000/(data['Gross Generation-Actual-' + unit].sum()*1000/60)

        #SHS Page
        #MS FLow = data['Superheat Spray Flows-Actual-BR3']*3
        #Total SHS  Flow= data['Superheat Spray Flows-Actual-BR3'] * 2
        #SHSF % = SHSF / MSF * 100
        #Deviation = SHSF% - SHS Target, SHS target = 0
        #% Unit Rating = data['Gross Generation-Actual-BR3']/GrossUnitRating_BR3
        #HREF = = -0.000193*N**2 + 0.0429*N - 0.37, N = % UR
        #Change in GTHR = Deviation * HREF if Deviation >0 , otherwies 0 
        #Change in GUHR = GTHR/(Boiler Effieciency / 100)
        if 'Superheat Spray Flows' in inputParameters:
            data['SHS_Deviation-' + unit] = ((data['Superheat Spray Flows-Actual-' + unit])/(data['Main Steam Flow-Actual-' + unit]) * 100 - constants[unit]['SHS_Target'])
            data['SHS_UnitRating-' + unit] = (data['Gross Generation-Actual-' + unit]/constants[unit]['GrossUnitRating'] * 100)
            data['SHS_HREF-' + unit] = -0.000193*(data['SHS_UnitRating-' + unit])**2 + 0.0429*data['SHS_UnitRating-' + unit] - 0.37 

            data['SHS_ChangeHeatInput-' + unit] = data.apply(lambda x: x['SHS_HREF-' + unit]*x['SHS_Deviation-' + unit]  if x['SHS_Deviation-' + unit] > 0 else 0 , axis=1) /(constants[unit]['boilerEfficiency']/100)  * data['Gross Generation-Actual-' + unit] * 1000/ (1000000*60)
            data['SHS_CostOfDeviation-' + unit] = data['SHS_ChangeHeatInput-' + unit] *data['Cost of Coal - High Sulfur-Actual-'+unit[:2]] #Coal Cost
            data['SHS_GUHR_Impact-' + unit] = data['SHS_ChangeHeatInput-' + unit]*1000000/(data['Gross Generation-Actual-' + unit].sum()*1000/60) if data['Gross Generation-Actual-' + unit].sum() > 0 else 0

        #RHS
        #Identifcal to SHS except difference in HREF equation. In addition CHange GTHR doesn't account for Deviation
        if 'Reheat Spray Flows' in inputParameters:
            data['RHS_Deviation-' + unit] = ((data['Reheat Spray Flows-Actual-' + unit])/(data['Main Steam Flow-Actual-' + unit]) * 100 - constants[unit]['RHS_Target'])
            data['RHS_UnitRating-' + unit] = (data['Gross Generation-Actual-' + unit]/constants[unit]['GrossUnitRating'] * 100)
            data['RHS_HREF-' + unit] = -0.00122*(data['RHS_UnitRating-' + unit])**2 + 0.255*data['RHS_UnitRating-' + unit] + 3.42
            data['RHS_ChangeHeatInput-' + unit] = data['RHS_HREF-' + unit]*data['RHS_Deviation-' + unit] /(constants[unit]['boilerEfficiency']/100)  * data['Gross Generation-Actual-' + unit] * 1000/ (1000000*60)
            data['RHS_CostOfDeviation-' + unit] = data['RHS_ChangeHeatInput-' + unit] *data['Cost of Coal - High Sulfur-Actual-'+unit[:2]] #Coal Cost
            data['RHS_GUHR_Impact-' + unit] = data['RHS_ChangeHeatInput-' + unit]*1000000/(data['Gross Generation-Actual-' + unit].sum()*1000/60) if data['Gross Generation-Actual-' + unit].sum() > 0 else 0

        #Excess 02
        if 'Boiler/Economizer O2' in inputParameters:
            data['O2_Deviation-' + unit] = data['Boiler/Economizer O2-Actual-' + unit]- data['Boiler/Economizer O2-Target-' + unit]
            data['O2_ChangeHeatInput-' + unit] = data['O2_Deviation-' + unit] * constants[unit]['HREF_O2'] * data['Gross Generation-Actual-' + unit] * 1000/1000000/60
            data['O2_CostOfDeviation-' + unit] = data['O2_ChangeHeatInput-' + unit] * data['Cost of Coal - High Sulfur-Actual-'+unit[:2]]  #Coal Cost
            data['O2_GUHR_Impact-' + unit] = data['O2_ChangeHeatInput-' + unit]*1000000/(data['Gross Generation-Actual-' + unit].sum()*1000/60) if data['Gross Generation-Actual-' + unit].sum() > 0 else 0

        if 'Main Steam Temperature' in inputParameters:
            data['MST_ChangeHeatInput-' + unit] = ((((data['Main Steam Temperature-Actual-' + unit]-data['Main Steam Temperature-Target-' + unit])*constants[unit]['HREF_MST'])/(constants[unit]['boilerEfficiency']/100))*data['Gross Generation-Actual-' + unit]*1000)/(1000000*60)
            data['MST_CostofDeviation-' + unit] = data['MST_ChangeHeatInput-' + unit]*data['Cost of Coal - High Sulfur-Actual-'+unit[:2]] 
            data['MST_TimeAboveTarget-' + unit] = ((data['Main Steam Temperature-Actual-' + unit]-data['Main Steam Temperature-Target-' + unit])>0).astype(int)
            data['MST_GUHR_Impact-' + unit] = data['MST_ChangeHeatInput-' + unit]*1000000/(data['Gross Generation-Actual-' + unit].sum()*1000/60) if data['Gross Generation-Actual-' + unit].sum() > 0 else 0
        if 'Main Steam Pressure' in inputParameters:
            data['MSP_ChangeHeatInput-' + unit] =(((data['Main Steam Pressure-Actual-' + unit]-data['Main Steam Pressure-Target-' + unit])*constants[unit]['HREF_MSP'])/(constants[unit]['boilerEfficiency']/100))*data['Gross Generation-Actual-' + unit]*1000/(1000000*60)
            data['MSP_CostofDeviation-' + unit] = data['MSP_ChangeHeatInput-' + unit]*data['Cost of Coal - High Sulfur-Actual-'+unit[:2]] 
            data['MSP_GUHR_Impact-' + unit] = data['MSP_ChangeHeatInput-' + unit]*1000000/(data['Gross Generation-Actual-' + unit].sum()*1000/60) if data['Gross Generation-Actual-' + unit].sum() > 0 else 0
            data['Percent_Unit_Rating-' + unit] = data['Gross Generation-Actual-'+unit]/constants[unit]['GrossUnitRating'] * 100
        if 'Hot Reheat Temp' in inputParameters:
            data['RHT_HREF-' + unit] = (-0.000174*(data['Percent_Unit_Rating-' + unit]**2)) + (0.0365*data['Percent_Unit_Rating-' + unit]) - 2.9 
            data['RHT_ChangeHeatInput-' + unit] = ((data['RHT_HREF-' + unit]*(data['Hot Reheat Temp-Actual-' + unit]-data['Hot Reheat Temp-Target-' + unit]))/(constants[unit]['boilerEfficiency']/100))*data['Gross Generation-Actual-' + unit]*1000/(1000000*60)
            data['RHT_CostofDeviation-' + unit] = data['RHT_ChangeHeatInput-' + unit]*data['Cost of Coal - High Sulfur-Actual-'+unit[:2]] 
            data['RHT_TimeAboveTarget-' + unit] = ((data['Hot Reheat Temp-Actual-' + unit]-data['Hot Reheat Temp-Target-' + unit])>0).astype(int)
            data['RHT_GUHR_Impact-' + unit] = data['RHT_ChangeHeatInput-' + unit]*1000000/(data['Gross Generation-Actual-' + unit].sum()*1000/60) if data['Gross Generation-Actual-' + unit].sum() > 0 else 0
            
        if 'Condenser Pressure' in inputParameters:
            data[f'AEP_Condenser_Duty-{unit}']      = constants[unit]['Condenser Duty c1'] * data[f'Main Steam Flow-Actual-{unit}'] + constants[unit]['Condenser Duty c2']

            if f'Condenser Pressure-Actual-{unit}' not in data.columns:
                data[f'Condenser Pressure-Actual-{unit}'] = (data[f'Condenser Pressure LP-Actual-{unit}']+data[f'Condenser Pressure HP-Actual-{unit}'])/2
                data[f'AEP_Condenser_Duty-{unit}'] = data[f'AEP_Condenser_Duty-{unit}'] * constants[unit]['LP Condenser Duty %']

            data[f'AEP_CW_Temp_Rise-{unit}']        = data[f'AEP_Condenser_Duty-{unit}'] * 1000000 / (500 * constants[unit]['CWF'])
            data[f'AEP_CW_Outlet_Temp-{unit}']      = data[f'Condenser Inlet Temp-Actual-{unit}'] + data[f'AEP_CW_Temp_Rise-{unit}']
            data[f'AEP_CW_Velocity-{unit}']         = (constants[unit]['CWF']/60/7.48 ) / ((math.pi * (constants[unit]['TubeID']/12)**2 / 4) * constants[unit]['NT'])
            data[f'AEP_HEI_CWIT_Correction-{unit}'] = data[f'Condenser Inlet Temp-Actual-{unit}'].apply(hei_correction)
            data[f'AEP_Heat_Transfer_Coeff-{unit}'] = constants[unit]['HEI_CoEff_U'] * np.sqrt(data[f'AEP_CW_Velocity-{unit}']) * \
                                                      data[f'AEP_HEI_CWIT_Correction-{unit}'] * constants[unit]['HEI_Tube_Mat_CoEf'] * constants[unit]['Tube_Cleaniness_Factor']
            data[f'AEP_Constant_R-{unit}']          = data[f'AEP_Heat_Transfer_Coeff-{unit}'] * constants[unit]['Tube_Surface_Area'] / (500 * constants[unit]['CWF'])
            data[f'AEP_Condenser_Vapor_Temp-{unit}']= (data[f'Condenser Inlet Temp-Actual-{unit}'] - (data[f'AEP_CW_Outlet_Temp-{unit}'] * np.exp(data[f'AEP_Constant_R-{unit}']))) / (1 - np.exp(data[f'AEP_Constant_R-{unit}']))
            data[f'AEP_Psat(Ts)-{unit}']            = data[f'AEP_Condenser_Vapor_Temp-{unit}'].apply(pressure_saturation)
            data[f'AEP_Terminal_Temp_Diff-{unit}']  = data[f'AEP_Condenser_Vapor_Temp-{unit}'] - data[f'AEP_CW_Outlet_Temp-{unit}']
            data[f'AEP_Alt_Cond_Vapr_Temp-{unit}']  = data[f'AEP_CW_Outlet_Temp-{unit}'] + 5
            data[f"AEP_Psat(Ts')-{unit}"]           = data[f'AEP_Alt_Cond_Vapr_Temp-{unit}'].apply(pressure_saturation)
            data[f'AEP_Target-{unit}']              = np.where(data[f'AEP_Terminal_Temp_Diff-{unit}'] < 5, data[f"AEP_Psat(Ts')-{unit}"], data[f'AEP_Psat(Ts)-{unit}'])

            if f'Condenser Pressure HP-Actual-{unit}' in data.columns:
                data[f'AEP_HP_Condenser_Duty-{unit}']       = (data[f'AEP_Condenser_Duty-{unit}'] / constants[unit]['LP Condenser Duty %']) * (1 - constants[unit]['LP Condenser Duty %'])
                data[f'AEP_HP_CW_Temp_Rise-{unit}']         = data[f'AEP_HP_Condenser_Duty-{unit}'] * 1000000 / (500 * constants[unit]['CWF'])
                data[f'AEP_HP_CW_Outlet_Temp-{unit}']       = data[f'AEP_CW_Outlet_Temp-{unit}'] + data[f'AEP_HP_CW_Temp_Rise-{unit}']
                data[f'AEP_HP_CW_Velocity-{unit}']          = (constants[unit]['CWF']/60/7.48 ) / ((math.pi * (constants[unit]['TubeID']/12)**2 / 4) * constants[unit]['NT_HP'])
                data[f'AEP_HP_HEI_CWIT_Correction-{unit}']  = data[f'AEP_CW_Outlet_Temp-{unit}'].apply(hei_correction)
                data[f'AEP_HP_Heat_Transfer_Coeff-{unit}']  = constants[unit]['HEI_CoEff_U'] * np.sqrt(data[f'AEP_HP_CW_Velocity-{unit}']) * \
                                                              data[f'AEP_HP_HEI_CWIT_Correction-{unit}'] * constants[unit]['HEI_Tube_Mat_CoEf'] * constants[unit]['Tube_Cleaniness_Factor']
                data[f'AEP_HP_Constant_R-{unit}']           = data[f'AEP_HP_Heat_Transfer_Coeff-{unit}'] * constants[unit]['Tube_Surface_Area_HP'] / (500 * constants[unit]['CWF'])
                data[f'AEP_HP_Condenser_Vapor_Temp-{unit}'] = (data[f'AEP_CW_Outlet_Temp-{unit}'] - (data[f'AEP_HP_CW_Outlet_Temp-{unit}'] * np.exp(data[f'AEP_HP_Constant_R-{unit}']))) / (1 - np.exp(data[f'AEP_HP_Constant_R-{unit}']))
                data[f'AEP_HP_Psat(Ts)-{unit}']             = data[f'AEP_HP_Condenser_Vapor_Temp-{unit}'].apply(pressure_saturation)
                data[f'AEP_HP_Terminal_Temp_Diff-{unit}']   = data[f'AEP_HP_Condenser_Vapor_Temp-{unit}'] - data[f'AEP_HP_CW_Outlet_Temp-{unit}']
                data[f'AEP_HP_Alt_Cond_Vapr_Temp-{unit}']   = data[f'AEP_HP_CW_Outlet_Temp-{unit}'] + 5
                data[f"AEP_HP_Psat(Ts')-{unit}"]            = data[f'AEP_HP_Alt_Cond_Vapr_Temp-{unit}'].apply(pressure_saturation)
                data[f'AEP_LP_Target-{unit}']               = data[f'AEP_Target-{unit}']
                data[f'AEP_HP_Target-{unit}']               = np.where(data[f'AEP_HP_Terminal_Temp_Diff-{unit}'] < 5, data[f"AEP_HP_Psat(Ts')-{unit}"], data[f'AEP_HP_Psat(Ts)-{unit}'])
                data[f'AEP_Target-{unit}']                  = (data[f'AEP_LP_Target-{unit}'] + data[f'AEP_HP_Target-{unit}']) / 2

            data[f'AEP_GTHR_CF_Std-{unit}']         = 1 + (constants[unit]['AEPHR'](data[f'Main Steam Flow-Actual-{unit}']*1000, data[f'Condenser Pressure-Actual-{unit}']) / 100)
            data[f'AEP_GTHR_CF_Target-{unit}']      = 1 + (constants[unit]['AEPHR'](data[f'Main Steam Flow-Actual-{unit}']*1000, data[f'AEP_Target-{unit}']) / 100)
            data[f'AEP_GTHR_Corrected-{unit}']      = data[f'Heat Rate-Actual-{unit}'] / data[f'AEP_GTHR_CF_Std-{unit}'] * data[f'AEP_GTHR_CF_Target-{unit}']
            data[f'AEP_GTHR_ActTar_Diff-{unit}']    = data[f'Heat Rate-Actual-{unit}'] - data[f'AEP_GTHR_Corrected-{unit}']
            data[f'AEP_ChangeInGTHR-{unit}']        = data[f'AEP_GTHR_ActTar_Diff-{unit}'] / (constants[unit]['boilerEfficiency']/100)
            data[f'AEP_ChangeInHeatInput-{unit}']   = data[f'AEP_ChangeInGTHR-{unit}'] * data[f'Gross Generation-Actual-{unit}']*1000 / (1000000*60)
            data[f'AEP_CostOfDeviation-{unit}']     = data[f'AEP_ChangeInHeatInput-{unit}'] * data[f'Cost of Coal - High Sulfur-Actual-{unit[:2]}'] 
            data[f'AEP_GUHR_Impact-{unit}']         = data[f'AEP_ChangeInHeatInput-{unit}'] * 1000000/(data[f'Gross Generation-Actual-{unit}'].sum()*1000/60) if data[f'Gross Generation-Actual-{unit}'].sum() > 0 else 0

            
            
        data = data.replace([np.inf, -np.inf], np.nan)
        if audit:
            auditQuery = f"UPDATE \"PI\".\"DCO_Audit\" SET \"CALC\" = True WHERE \"ID\" = {audits[unit]}"
            dbConnection.execute(auditQuery)
    return data, audits

    
def dcoSave(data:pd.DataFrame,audits:dict = {}):
    time = data.index
    pdwStart = min(time)
    pdwEnd = max(time)
    est = (datetime.utcnow()-timedelta(hours=5)).hour == datetime.now().hour
    time = time.strftime("%Y-%m-%d %H:%M:%S").tolist()

    if not est:
        pdwStart = pdwStart -timedelta(hours=1)
        pdwEnd = pdwEnd -timedelta(hours=1)
    #all units have gross load parameter
    units = [c.split('-')[2] for c in data.columns if 'Gross Generation' in c]
    
    TagQuery = f"""
    SELECT 
        "TAGID"
        ,"PiTag"
    FROM "PI"."DCO_OutputParameters" 
    """
    outputParameters = pExtractPostgres(TagQuery)

    for unit in units:
        #queue = Queue()
        #processes= []
        arguments = []
        #Creating process to run all the datauploads at same time instead of foor looping
        #Consider moving to a pool instead of processes to make sure it doens't break
        #You can make too many processes and it will crash.
        for index, row in outputParameters[outputParameters['PiTag'].str.contains(shortToLongPU(unit))].iterrows():
            try:
                #for tag in outputParameters:
                tag = row['PiTag']
                #print(tag)
                #I believe we overwrite values in PI
                values = data[TagToVar(tag)].values.tolist()
                #processes.append(Process(target=savePiValues, args=(tag,values,time)))
                arguments.append([tag,values,time])
            except KeyError as e:
                #print(e)
                continue
        with Pool(processes = 8) as pool:
            try:
                r = pool.starmap_async(savePiValues, arguments)
                r.wait()
            except Exception as e:
                print(f'Failed with: {e}\n')
        #UPLOADING TO PI
        #for p in processes:
        #        p.start()
        #for p in processes:
        #    try:
        #       p.join()
        #    except TypeError:
        #        t = 1
        #        print('SOmething broke', TypeError)
        #    finally:
        #        p.close()
        #queue.close()
        if audits != {}:
            auditQuery = f"UPDATE \"PI\".\"DCO_Audit\" SET \"PI\" = True WHERE \"ID\" = {audits[unit]}"
            dbConnection.execute(auditQuery)
        data = data.tz_localize(None)
        print('PDW')
        
        #You could alternatively create an insert for each tag and then concat all the inserts to do one bulk insert
        for index, row in outputParameters[outputParameters['PiTag'].str.contains(shortToLongPU(unit))].iterrows():
            try:
                #Need to create insert first to check if we even calculated that value, otherwise we'll get an index error
                insert = data[TagToVar(row['PiTag'])].to_frame()
                insert =insert.reset_index()
                insert['tag'] = row['TAGID']
                if(est):
                    insert['time'] = insert.time.dt.tz_localize(None)
                else:
                    insert['time'] = insert.time.dt.tz_localize(None) -timedelta(hours=1)
                insert = insert.rename(columns={TagToVar(row['PiTag']):'value'})
                
                #insert is ready, delete and then run insert
                delete = alchemyEngine.execute(f"DELETE from \"PI\".\"PIInterp\" WHERE \"tag\" ={row['TAGID']} AND \"time\" between '{datetime.strftime(pdwStart, '%Y%m%d %H%M%S')}' AND '{datetime.strftime(pdwEnd, '%Y%m%d %H%M%S')}'")
                
                insert.to_sql(schema= 'PI', name='PIInterp', con=alchemyEngine, if_exists='append', index=False)
            except:
                print('skipping',TagToVar(row['PiTag']))
        if audits != {}:
            auditQuery = f"UPDATE \"PI\".\"DCO_Audit\" SET \"INTERP\" = True WHERE \"ID\" = {audits[unit]}"
            dbConnection.execute(auditQuery)
#Runs the DCO prcoess Production version with sys arguments and auditing.
if __name__ == '__main__':
    #note that sys.argv[0] is file name, so min size 1 and skip 0 index 

    #defult runs millcreek
    plants = sys.argv[1].split(',') if len(sys.argv) >= 2 else ['MC'] 
    BR = ['BR3']
    GH = ['GH1', 'GH2' , 'GH3' , 'GH4']
    MC =  ['MC1', 'MC2' , 'MC3' , 'MC4']
    TC = ['TC1', 'TC2']

    #https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists
    units = [item for sublist in plants for item in eval(sublist)]
    print(units)
    shift = sys.argv[2] if len(sys.argv) >= 3 else 5
    shiftStart,shiftEnd= latestShift(shift)
    print(shiftStart,shiftEnd)
    #explicitly pointed so you don't mess it up.
    #inputParameters = [] disgnates all parametesr
    data, audits = dcoProcess(units = units,piStart = shiftStart, piEnd = shiftEnd,inputParameters = [], audit = True)
    print('data done')
    dcoSave(data,audits)
    print('save done')
