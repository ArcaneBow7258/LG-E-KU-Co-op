DROP TABLE IF EXISTS tmp; CREATE TEMP TABLE tmp (time timestamp, unit_id text, setpoint numeric, actgrossgen numeric, ramprate numeric,
												controlmode numeric, blockhigh numeric, blocklow numeric, ramprateunfilt numeric,
												 ramprateunfiltprev numeric, ramprateunfiltnext numeric,
												ramprateunfiltfinal numeric, ActualRampPct numeric, prevactgrossgen numeric);
copy tmp from 
'/u01/JupyterFolder/Test/Analysis/AlvinCode/Ramp Rate/EMSData20220101_000000_1month.csv'  delimiter ',' csv null as 'NULL'header ;

with thresh as (
SELECT EXTRACT(month from timestamp '20220101') as time, unit_id, avg(param."TARGETRAMP") as targetramp, sum(ems.ActualRampPct) as ActualRampPct, param."ISCT" as ISCT, avg(ramprate) as avgramprate 
FROM tmp ems join "PI"."RampRateParameters" param on ems.UNIT_ID = param."UNIT_ID"
GROUP BY ems.unit_id, EXTRACT(month from timestamp '20220101'), param."ISCT" )
,counts as (SELECT UNIT_ID, time, targetRamp, ActualRampPct, ISCT,avgramprate,
"PI".RampRate_PlantCount('20220101 000000', UNIT_ID)  countRecs,
 "PI".RampRate_ControlMode('20220101 000000', UNIT_ID) countAGCOn,
 "PI".RampRate_TargetRamp('20220101 000000', UNIT_ID) countAtTgtRamp,
  "PI".RampRate_Ramppct('20220101 000000', UNIT_ID) countActRampPct
FROM thresh)

,pct as (SELECT UNIT_ID, time, targetRamp, ISCT,
countRecs,  countAGCOn, countAtTgtRamp,countActRampPct,
case when countAGCon > 0 then
round((countAGCon / countRecs) * 100) else 0 end as pctAGCOn,
case when countAtTgtRamp >0 then
round((countAtTgtRamp / countRecs) *100) else 0 end as pctTimeTgtRamp,
case when ActualRampPct >0 then
round((ActualRampPct / countActRampPct) *100) else 0 end as ActualRampPct, avgramprate
FROM counts)

,almost as (SELECT UNIT_ID, time, pctAGCOn, targetRamp, pctTimeTgtRamp,
		ActualRampPct,
		round(targetramp * (ActualRampPct / 100), 2) as actRampRate,
		--pctTimeAGCOn, pctTimeTargetRampRate, pctActRampPct, station,
		countRecs, countAGCon, countAtTgtRamp, countActRampPct, isct, avgramprate
		FROM pct)

SELECT UNIT_ID,time,countRecs, countAGCon, countAtTgtRamp, countActRampPct, actRampRate,
case when countAGCon = 0 then null else case when pctAGCOn = 0 then 0 else pctAGCOn end end as pctAGCOn,
case when countAtTgtRamp = 0 then null else case when targetramp = 0 then 0 else targetramp end end as targetramp,
case when countActRampPct = 0 then null else case when pctTimeTgtRamp = 0 then 0 else pctTimeTgtRamp end end as pctTimeTgtRamp,
case when ActualRampPct = 0 then null else ActualRampPct end as ActualRampPct, 
case when pctAGCOn > 75 then 1 else 0 end as agcOnThresh,
case when pctTimeTgtRamp > 75 then 1 else 0 end as timeTargetRampThresh,

case when ActualRampPct > 70 then 1 else 0 end as actRampPctThresh,  avgramprate, isct

FROM almost
WHERE countagcon <> 0 AND countattgtramp <> 0 
ORDER BY UNIT_ID