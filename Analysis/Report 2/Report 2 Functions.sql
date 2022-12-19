CREATE OR REPLACE FUNCTION "PI".RampRate_PlantCount(in pTime timestamp,in pUnitID varchar, out res numeric ) RETURNS numeric 
as
$$
BEGIN
SELECT count(*) INTO res
FROM tmp ed join "PI"."RampRateParameters" rrp on ed.UNIT_ID = rrp."UNIT_ID"
WHERE ed.UNIT_ID = rrp."UNIT_ID"
 and EXTRACT(year from ed.time) = EXTRACT(year from pTime)
 and EXTRACT(month from ed.time) = EXTRACT(month from pTime)
and ed.unit_id = pUnitID;
END $$
 LANGUAGE plpgsql;
 
 CREATE OR REPLACE FUNCTION "PI".RampRate_ControlMode(in pTime timestamp,in pUnitID varchar, out res numeric ) RETURNS numeric 
as
$$
BEGIN
SELECT count(*) INTO res
FROM tmp ed join "PI"."RampRateParameters" rrp on ed.UNIT_ID = rrp."UNIT_ID"
WHERE ed.UNIT_ID = rrp."UNIT_ID"
 and EXTRACT(year from ed.time) = EXTRACT(year from pTime)
 and EXTRACT(month from ed.time) = EXTRACT(month from pTime)
and ed.unit_id = pUnitID
and (ed.controlmode = 6 or ed.controlmode = 3 and pUnitID in ('TC1', 'TC2'))
and ed.actgrossgen >= rrp."MINREPORTINGGEN"
and ed.actgrossgen <= rrp."MAXLOAD";
END $$
 LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION "PI".RampRate_RampPct(in pTime timestamp,in pUnitID varchar, out res numeric ) RETURNS numeric 
as
$$
BEGIN
SELECT count(*) INTO res
FROM tmp ed join "PI"."RampRateParameters" rrp on ed.UNIT_ID = rrp."UNIT_ID"
WHERE ed.UNIT_ID = rrp."UNIT_ID"
 and EXTRACT(year from ed.time) = EXTRACT(year from pTime)
 and EXTRACT(month from ed.time) = EXTRACT(month from pTime)
and ed.unit_id = pUnitID
and ed.actRampPct is not null
and ed.actgrossgen >= rrp."MINREPORTINGGEN"
and ed.actgrossgen <= rrp."MAXLOAD"
;
END $$
 LANGUAGE plpgsql;
 
CREATE OR REPLACE FUNCTION "PI".RampRate_TargetRamp(in pTime timestamp,in pUnitID varchar, out res numeric ) RETURNS numeric 
as
$$
BEGIN
SELECT count(*) INTO res
FROM (SELECT ems.*,
	  case when ((ems.actgrossgen < rrp."HALFRAMPTARGETLOAD") and (ems.actgrossgen > rrp."LOWOPERATINGLOAD"))  then
	  	case when ems.ramprate >= rrp."MATCHTARGETRAMP" * rrp."TARGETRAMP" then 1 end
	  end as count1,
	  case when ems.actgrossgen >= rrp."HALFRAMPTARGETLOAD" then 
	  	case when ems.ramprate >= rrp."MATCHTARGETRAMP"   * rrp."REDUCEDRAMPTARGET" then 1 end
	  end as count2,
	  case when ems.actgrossgen <= rrp."LOWOPERATINGLOAD" then
	  	case when ems.ramprate >= rrp."MATCHTARGETRAMP"  * rrp."LOWOPERATINGRAMPTARGET" then 1 end
	  end as count3
	  from
	  tmp ems join "PI"."RampRateParameters" rrp on ems.UNIT_ID = rrp."UNIT_ID"
	  
	  WHERE
	  ems.UNIT_ID = rrp."UNIT_ID"
	 and EXTRACT(year from ems.time) = EXTRACT(year from pTime)
	 and EXTRACT(month from ems.time) = EXTRACT(month from pTime)
	 and ems.UNIT_ID = pUnitID
 	 and ems.actgrossgen >= rrp."MINREPORTINGGEN"
 	 and ems.actgrossgen <= rrp."MAXLOAD") a
	 WHERE (count1 = 1 or count2 = 1 or count3 = 1)

;
END $$
 LANGUAGE plpgsql;
 
