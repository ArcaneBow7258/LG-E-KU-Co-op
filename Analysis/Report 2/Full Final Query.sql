DROP TABLE IF EXISTS emsTemp; 
with emsTags as (SELECT * FROM (SELECT *, CASE "PLANT_PI" WHEN 'Brown' then CONCAT('BR' ,SUBSTRING("UNIT_PI", 2))
WHEN 'Trimble' then CONCAT('TC' ,SUBSTRING("UNIT_PI", 2))
WHEN 'Ghent' then CONCAT('GH' ,SUBSTRING("UNIT_PI", 2))
WHEN 'CaneRun' then CONCAT('CR' ,SUBSTRING("UNIT_PI", 2))
WHEN 'MillCreek' then CONCAT('MC' ,SUBSTRING("UNIT_PI", 2)) 
end as UNIT_ID
				 FROM ((SELECT t."TAGID_PI", "OLD_TAGID_PI", "TAG_PI", "PLANT_PI", "UNIT_PI", "IsInterp", "IsStep", digitalset, "POINT_TYPE", "LastInterpValue"
FROM "PI"."PITAG" t RIGHT JOIN "PI"."RampRatePointType" p on t."OLD_TAGID_PI" = p."TAGID_PI" 
WHERE "TAG_PI" LIKE 'EMS%') 
			   UNION 
			   (SELECT t."TAGID_PI", "OLD_TAGID_PI", "TAG_PI", "PLANT_PI", "UNIT_PI","IsInterp", "IsStep", digitalset, "POINT_TYPE", "LastInterpValue"
FROM "PI"."PITAG" t RIGHT JOIN "PI"."RampRatePointType" p on t."TAGID_PI" = p."TAGID_PI" 
WHERE "TAG_PI" LIKE 'EMS%')) a) a LEFT JOIN "PI"."RampRateParameters" param ON a.UNIT_ID = param."UNIT_ID"
WHERE NOT ("TAGID_PI" = 1401620332 AND "POINT_TYPE" = 'Blocked Low')),
emsTagsStaging as (select * from emsTags WHERE UNIT_ID in ('BR3', 'CR7', 'GH1', 'GH2', 'GH3', 'GH4','MC1', 'MC2', 'MC3', 'MC4', 'TC1', 'TC2')),
emsTimes as (SELECT cur."time" as time , "TAGID_PI",  "POINT_TYPE", "TAG_PI", t.UNIT_ID, cur.value as emsvalue, 
			 LEAD(value, 1) OVER (PARTITION BY tag ORDER BY time) emsvaluenext, 
			 LAG(value, 1) OVER (PARTITION BY tag ORDER BY time)  emsvalueprev, 
			 LAG(value, 2) OVER (PARTITION BY tag ORDER BY time) emsvalueprev2,
			 "MAXLOAD", "HALFRAMPTARGETLOAD", "TARGETRAMP", "MAXRAMP", "MATCHTARGETRAMP", "REDUCEDRAMPTARGET", "MINREPORTINGGEN", "LOWOPERATINGLOAD", "LOWOPERATINGRAMPTARGET", "ISCT"

FROM
"PI"."PIInterp" cur  INNER JOIN emsTags t ON cur."tag" = t."TAGID_PI"
WHERE cur."time" between ( date_trunc('month', NOW()::timestamp - interval '1 month') - interval '2 minute') 
			 AND date_trunc('month', NOW()::timestamp - interval '1 month') + interval '1 day 1 minute')

,seperate as (SELECT UNIT_ID, time, "MAXLOAD", "HALFRAMPTARGETLOAD", "TARGETRAMP", "MAXRAMP", "MATCHTARGETRAMP", "REDUCEDRAMPTARGET", "MINREPORTINGGEN", "LOWOPERATINGLOAD", "LOWOPERATINGRAMPTARGET", "ISCT",


				case  "POINT_TYPE"  
					when 'Ramp Rate' then emsvalue  
					end as RampRate,  

					case  "POINT_TYPE"  
					when 'Ramp Rate' then emsValuePrev  
					end as PrevRampRate,  

					case  "POINT_TYPE"  
					when 'Ramp Rate' then emsValueNext  
					end as NextRampRate,  

					case  "POINT_TYPE"  
					when 'Ramp Rate' then emsValuePrev2  
					end as Prev2RampRate,  

					-- Set Points
					case  "POINT_TYPE"  
					when 'Setpoint' then emsvalue  
					end as SetPoint,  

					case  "POINT_TYPE"  
					when 'Setpoint' then emsValuePrev  
					end as PrevSetPoint,  

					case  "POINT_TYPE"  
					when 'Setpoint' then emsValueNext  
					end as NextSetPoint,  

					case  "POINT_TYPE"  
					when 'Setpoint' then emsValuePrev2  
					end as Prev2SetPoint,  

					-- Act Gross Generations
					case  "POINT_TYPE" 
					when 'Act. Gross Gen' then emsvalue 
					end as ActGrossGen, 

					case  "POINT_TYPE" 
					when 'Act. Gross Gen' then emsvaluePrev 
					end as PrevActGrossGen, 

					case  "POINT_TYPE" 
					when 'Act. Gross Gen' then emsvalueNext 
					end as NextActGrossGen, 

					case  "POINT_TYPE" 
					when 'Act. Gross Gen' then emsvaluePrev2 
					end as Prev2ActGrossGen, 

					-- Control modes
					case  "POINT_TYPE" 
					when 'Control Mode' then emsvalue 
					end as ControlMode, 

					case  "POINT_TYPE" 
					when 'Control Mode' then emsvaluePrev 
					end as PrevControlMode, 

					case  "POINT_TYPE" 
					when 'Control Mode' then emsvalueNext 
					end as NextControlMode, 

					case  "POINT_TYPE" 
					when 'Control Mode' then emsvaluePrev2 
					end as Prev2ControlMode, 

					-- Blocked Highs
					case  "POINT_TYPE" 
					when 'Blocked High' then emsvalue 
					end as BlockHigh, 

					case  "POINT_TYPE" 
					when 'Blocked High' then emsvaluePrev 
					end as PrevBlockHigh, 

					case  "POINT_TYPE" 
					when 'Blocked High' then emsvalueNext 
					end as NextBlockHigh, 

					case  "POINT_TYPE" 
					when 'Blocked High' then emsvaluePrev2 
					end as Prev2BlockHigh, 

					-- Blocked Lows
					case  "POINT_TYPE" 
					when 'Blocked Low' then emsvalue 
					end as BlockLow, 

					case  "POINT_TYPE" 
					when 'Blocked Low' then emsvaluePrev 
					end as PrevBlockLow, 

					case  "POINT_TYPE" 
					when 'Blocked Low' then emsvalueNext 
					end as NextBlockLow, 

					case  "POINT_TYPE" 
					when 'Blocked Low' then emsvaluePrev2 
					end as Prev2BlockLow 

FROM emsTimes WHERE time BETWEEN date_trunc('month', NOW()::timestamp - interval '1 month')
			  AND date_trunc('month', NOW()::timestamp - interval '1 month') + interval '1 day'),
agg as (SELECT  UNIT_ID, time, "MAXLOAD", "HALFRAMPTARGETLOAD", "TARGETRAMP", "MAXRAMP", "MATCHTARGETRAMP", "REDUCEDRAMPTARGET", "MINREPORTINGGEN", "LOWOPERATINGLOAD", "LOWOPERATINGRAMPTARGET", "ISCT",
		max(RampRate) as RampRate, max(PrevRampRate) as PrevRampRate, max(NextRampRate) as NextRampRate, 
				max(Prev2RampRate) as Prev2RampRate, 
				max(SetPoint) as SetPoint, max(PrevSetPoint) as PrevSetPoint, max(NextSetPoint) as NextSetPoint, 
				max(Prev2SetPoint) as Prev2SetPoint, 
				max(ActGrossGen) as ActGrossGen, max(PrevActGrossGen) as PrevActGrossGen, max(NextActGrossGen) as NextActGrossGen, 
				max(Prev2ActGrossGen) as Prev2ActGrossGen, 
				max(ControlMode) as ControlMode, max(PrevControlMode) as PrevControlMode, max(NextControlMode) as NextControlMode, 
				max(Prev2ControlMode) as Prev2ControlMode,  
				max(BlockHigh) as BlockHigh, max(PrevBlockHigh) as PrevBlockHigh, max(NextBlockHigh) as NextBlockHigh, 
				max(Prev2BlockHigh) as Prev2BlockHigh, 
				max(BlockLow) as BlockLow, max(PrevBlockLow) as PrevBlockLow, max(NextBlockLow) as NextBlockLow, 
				max(Prev2BlockLow) as Prev2BlockLow--, configmode 
		FROM seperate
GROUP BY time, unit_id,"MAXLOAD", "HALFRAMPTARGETLOAD", "TARGETRAMP", "MAXRAMP", "MATCHTARGETRAMP", "REDUCEDRAMPTARGET", "MINREPORTINGGEN", "LOWOPERATINGLOAD", "LOWOPERATINGRAMPTARGET", "ISCT"
ORDER BY unit_id, time, "MAXLOAD", "HALFRAMPTARGETLOAD", "TARGETRAMP", "MAXRAMP", "MATCHTARGETRAMP", "REDUCEDRAMPTARGET", "MINREPORTINGGEN", "LOWOPERATINGLOAD", "LOWOPERATINGRAMPTARGET", "ISCT")

,step1 as (SELECT *, case when abs(SetPoint - PrevSetPoint) > "MATCHTARGETRAMP" * RampRate
			and (ControlMode = 6 or ControlMode = 7 or (ControlMode=3 and unit_id in ('TC1','TC2')))
			and "MAXLOAD" > PrevActGrossGen 
			and ActGrossGen >= "MINREPORTINGGEN" 
			then abs(ActGrossGen - PrevActGrossGen) end as rampRateUnfilt, 

			case when abs(PrevSetPoint - Prev2SetPoint) > "MATCHTARGETRAMP" * PrevRampRate
			
			and (PrevControlMode = 6 or PrevControlMode = 7 or (PrevControlMode=3 and unit_id in ('TC1','TC2')))
			and PrevActGrossGen >= "MINREPORTINGGEN" 
			then abs(PrevActGrossGen - Prev2ActGrossGen) end as rampRateUnfiltPrev, 

			case when abs(NextSetPoint - SetPoint) >"MATCHTARGETRAMP" * NextRampRate
			and (NextControlMode = 6 or NextControlMode = 7 or (NextControlMode=3 and unit_id in ('TC1','TC2')))
			and NextActGrossGen >="MINREPORTINGGEN" 
			then abs(NextActGrossGen - ActGrossGen) end as rampRateUnfiltNext
			FROM agg)
			
,final as (SELECT *, case when rampRateUnfiltPrev > 0 or rampRateUnfiltNext > 0 
		then case when rampRateUnfilt > "MAXRAMP" 
			 then null 
			 else 
				case when rampRateUnfilt > 0 
				then rampRateUnfilt 
				else null end end 
		else null end as rampRateUnfiltFinal FROM step1)
,emsData as (SELECT time, unit_id, SetPoint, ActGrossGen, RampRate, ControlMode, BlockHigh, BlockLow, rampRateUnfilt, rampRateUnfiltPrev, rampRateUnfiltNext, rampRateUnfiltFinal, 
case when rampRateUnfiltFinal > 0 
	then case when prevActGrossGen >= "HALFRAMPTARGETLOAD" 
		 then rampRateUnfiltFinal/("REDUCEDRAMPTARGET") 
		 else rampRateUnfiltFinal / "TARGETRAMP" end 
	else null end as ActualRampPct, prevActGrossGen
FROM final)
SELECT * into emsTemp from emsData;
with thresh as (
SELECT EXTRACT(month from time) as time, unit_id, avg(param."TARGETRAMP") as targetramp, sum(ems.ActualRampPct) as actualRampPct, param."ISCT" as ISCT, avg(ramprate) as avgramprate 
FROM emsTemp ems join "PI"."RampRateParameters" param on ems.UNIT_ID = param."UNIT_ID"
GROUP BY ems.unit_id, EXTRACT(month from time), param."ISCT" )
,counts as (SELECT UNIT_ID, time, targetRamp, ActualRampPct, ISCT,avgramprate,
"PI".RampRate_PlantCount(date_trunc('month', NOW()::timestamp - interval '1 month'), UNIT_ID)  countRecs,
 "PI".RampRate_ControlMode(date_trunc('month', NOW()::timestamp - interval '1 month'), UNIT_ID) countAGCOn,
 "PI".RampRate_TargetRamp(date_trunc('month', NOW()::timestamp - interval '1 month'), UNIT_ID) countAtTgtRamp,
  "PI".RampRate_Ramppct(date_trunc('month', NOW()::timestamp - interval '1 month'), UNIT_ID) countActRampPct
FROM thresh)

,pct as (SELECT UNIT_ID, time, targetRamp, ISCT,avgramprate,
countRecs,  countAGCOn, countAtTgtRamp,countActRampPct,
case when countAGCon > 0 then
round((countAGCon / countRecs) * 100) else 0 end as pctAGCOn,
case when countAtTgtRamp >0 then
round((countAtTgtRamp / countRecs) *100) else 0 end as pctTimeTgtRamp,
case when ActualRampPct >0 then
round((ActualRampPct / countActRampPct) *100) else 0 end as ActualRampPct
FROM counts)

,almost as (SELECT UNIT_ID, time, pctAGCOn, targetRamp, pctTimeTgtRamp,avgramprate,
		ActualRampPct,
		round(targetramp * (ActualRampPct / 100), 2) as actRampRate,
		--pctTimeAGCOn, pctTimeTargetRampRate, pctActRampPct, station,
		countRecs, countAGCon, countAtTgtRamp, countActRampPct, isct
		FROM pct)
SELECT UNIT_ID,time,avgramprate,
case when countAGCon = 0 then null else case when pctAGCOn = 0 then 0 else pctAGCOn end end as pctAGCOn,
case when countAtTgtRamp = 0 then null else case when targetramp = 0 then 0 else targetramp end end as targetramp,
case when countActRampPct = 0 then null else case when pctTimeTgtRamp = 0 then 0 else pctTimeTgtRamp end end as pctTimeTgtRamp,
case when ActualRampPct = 0 then null else ActualRampPct end as ActualRampPct, 
case when pctAGCOn > .75 then 1 else 0 end as agcOnThresh,
case when pctTimeTgtRamp > .75 then 1 else 0 end as timeTargetRampThresh,
actRampRate,
case when ActualRampPct > .75 then 1 else 0 end as actRampPctThresh, isct,
countRecs, countAGCon, countAtTgtRamp, countActRampPct
FROM almost
ORDER BY UNIT_ID;
