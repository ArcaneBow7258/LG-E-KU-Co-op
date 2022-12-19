from DCOProcess import *
import sys
import urllib3
import math
import numpy as np
urllib3.disable_warnings()
sys.path.insert(1,'/u01/JupyterFolder/Production/Analysis/DataExtraction')
from pExtractData import *
alchemyEngine = create_engine('')
dbConnection = alchemyEngine.connect()

#Pulls in gaps in audit table
gapQuery = '''
        with noDups as (   SELECT distinct \"PLANT\",\"START\",\"END\" FROM \"PI\".\"DCO_Audit\"  WHERE \"INTERP\" is not null
			   )


        ,audit as (

        SELECT \"PLANT\",\"START\", LEAD(\"END\",1) over (PARTITION BY \"PLANT\" ORDER BY  \"END\" DESC) as lastEnd,
        rank() over (PARTITION BY \"PLANT\" ORDER BY  \"END\" DESC) FROM noDups

        )
        SELECT  \"PLANT\",\"START\",lastEnd FROM audit where lastEnd + interval '1 minute' < \"START\" GROUP BY \"PLANT\",\"START\", lastEnd
    ''' 
gaps = pExtractPostgres(gapQuery)

gaps = gaps.sort_values("PLANT")
#Starting with BR3, generates 12HR shifts to report to run as like the DCO Process
#Starts with the most recent gap
#generates forward from beginning of gap.
#Each shift takes about 2-3 minutes to run.
for gap in gaps.values:
    unit = gap[0]
    startGap = gap[2]
    endGap = gap[1]
    startEnds = pd.date_range(startGap, endGap, freq="12H")
    for idx, i in enumerate(startEnds):
        if idx + 1== len(startEnds):
            break
        estStart = i + timedelta(minutes = 1)
        estEnd =  startEnds[idx+1]
        piStart = estStart
        piEnd = estEnd
        est = (datetime.utcnow()-timedelta(hours=5)).hour == datetime.now().hour
        if(not est):
            piStart = piStart  +timedelta(hours=1)
            piEnd = piEnd +timedelta(hours=1)
        data,audits = dcoProcess(units = [unit],piStart = piStart, piEnd = piEnd,inputParameters = [], audit = True)
        dcoSave(data,audits)
