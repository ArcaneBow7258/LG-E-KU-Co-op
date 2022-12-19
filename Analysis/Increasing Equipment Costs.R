# 'dataset' holds the input data for this script
#query_data<-as.data.frame(dataset, stringsAsFactors = FALSE)
#Makes dataset into a "data frame" for usage
#factors are objects that categorize data and stores as "levels" like selection

#.libPaths("H:/")	
start.time = Sys.time()
#.libPaths("C:/RLibrary")  #turn off for powerBI
library(lme4)
#Sets library path; Linear mixed-effects (Like mat Lab?) Fits data
require("RColorBrewer")
require("ggplot2")
require("RODBC")
require("dplyr")

setwd("H:/") #This is where the .csv will be saved
#csv is saved as InreasingEquipmentCostsRank

db.con = odbcDriverConnect('driver={SQL Server};server=;database=;trusted_connection=true')
myQuery = paste0(
  "SELECT 
  	SUM(B.AMOUNT) AS Cost 
   ,A.LOCATION
   ,A.Loc_Name
   ,B.MONTH_NUMBER
   ,A.wonum WorkOrder
   ,A.PROBLEMCODE
   ,(left(A.Location, 5) + ': ' + L1.Description + ': ' + D.Description + ': *' + A.ProblemCode + '*') [EquipmentProblem]
   ,(left(A.Location, 5) + ': ' + L1.Description + ': ' + D.Description) [Equipment]
    ,A.FailureRemarks
    ,A.DESCRIPTION
    From [Generation].[agent].[MaximoWorkOrders] as A
    INNER JOIN [GenerationStaging].[dbo].[PowerPlan_CR_PowerGen] as b ON A.WONUM = B.task
    left join [PowerPlant_DW].[dbo].[CR_Structures_Flattened2] as ac on  ac.DETAIL_POINT = b.ACCOUNT
    left join [PowerPlant_DW].[dbo].[CR_Structures_Flattened2] as o on  o.DETAIL_POINT = b.ORGANIZATION
    left join [MaximoDW].[dbo].[Locations] as D on a.location = D.location
  	left join (	[MaximoDW].[dbo].[LocHierarchy] as H1
				left join [MaximoDW].[dbo].[Locations] as L1 
					on H1.Parent = L1.location
			) on a.Location = H1.location
  where o.element_description = 'Organization'  
  and o.SUMMARY_POINT_17 = 'P42100: GENERATION'
  and o.summary_point_16 = 'P42730: TRIMBLE COUNTY'
  and a.LOCATION like 'TC%'
  and a.PMPMNUM is null
  and ac.element_description = 'Account'  
  and ac.SUMMARY_POINT_20 = 'Account: <PPLTIS>'
  and ac.SUMMARY_POINT_18 in (
							  'PPLCTL: TOTAL COST OF SALES'
							  ,'PPLETO: TOTAL OPERATING EXPENSE'
							  ,'PPLOIE: TOTAL OTHER INCOME AND EXPENSE'
							  )
    and B.MONTH_NUMBER>200800
    GROUP BY A.LOCATION,
    A.Loc_Name,
    B.MONTH_NUMBER, 
    A.WONUM,
    A.PROBLEMCODE,
    (left(A.Location, 5) + ': ' + L1.Description + ': ' + D.Description + ': *' + A.ProblemCode + '*'),
    (left(A.Location, 5) + ': ' + L1.Description + ': ' + D.Description),
    A.FailureRemarks,
    A.DESCRIPTION
    ORDER BY A.LOCATION, B.MONTH_NUMBER;

  "
)#Same query as from old powerBI but I removed all comments
query_data = sqlQuery(db.con,myQuery) #Grab everything :)
odbcClose(db.con)
#loading in the data
query_data$Date = as.Date(paste(substring(query_data$MONTH_NUMBER,0,4), substring(query_data$MONTH_NUMBER,5,6), "01", sep="-" ))
#Mkaing a date column
end.time=Sys.time()
dataLoad.time = end.time-start.time #typically 42~ seconds as of 1/20/2022; Also this math doesnt actually work idk man
start.time=Sys.time()
#query_data<-read.csv("H:/OriginalData.csv", stringsAsFactors = FALSE)
#query_data$Date = as.Date(query_data$Date,  "%m/%d/%Y") #converts Date column from character to type - date
query_data$HalfYear=(paste(format(query_data$Date,  "%Y"), sprintf("%02i", (as.POSIXlt(query_data$Date)$mon%/%6)*6 +4),"1", sep="-")) ##Breaks the date into 6 month periods
#$ is the [] operator for columns. Essentially replaces the data into more acceptable formats
#sprintf; python print replace thing.
#concatination string paste()
#as.POSIXlt; Helps work with the Date fromat.q9


list_of_months<-seq(min(query_data$Date), max(query_data$Date),by="month") #creates a list of months
list_of_HalfYears=(paste(format(list_of_months,  "%Y"), sprintf("%02i", (as.POSIXlt(list_of_months)$mon%/%6)*6 +4),"1", sep="-")) ##Breaks the date into 6 month periods
list_of_HalfYears=unique(list_of_HalfYears)#list of half years
list_of_HalfYears = as.Date(list_of_HalfYears, "%Y-%m-%d") #converts Date column from character to type - date
list_of_locations<-unique(query_data$LOCATION)#creates a list of locations
rm(list_of_months) #deletes objects from memor


#create the table in the form we need
seed_table<-data.frame(LOCATION = sort(rep(list_of_locations, length(list_of_HalfYears))), HalfYear = rep(list_of_HalfYears,length(list_of_locations)), stringsAsFactors = FALSE )
#rep is replicate the list, length() times

#do the Half Year aggregation
agg_df<-aggregate(Cost ~ HalfYear + LOCATION, query_data, FUN = sum)
agg_df$HalfYear = as.Date(agg_df$HalfYear, "%Y-%m-%d") #converts HalfYear column from character to type - date
#Creates a  cost object with columns halfyear + Location, grouped by Query_data; Summed

#merge with list to fill in gaps with 0
combo<-merge(x = seed_table, y = agg_df, all = TRUE)
combo$Cost[is.na(combo$Cost)]<-0

  
  
# change data type
combo$LOCATION<-as.factor(combo$LOCATION)
combo$HalfYear<-as.Date(combo$HalfYear)


#run the linear regression
lr <- lmList(Cost ~ HalfYear | LOCATION, data=combo)

#Recent Regression
#Months 1-6 will aggregate to April HY, 7-12 will aggregate to October HalfYear. Eitherway, while we are in one range, we would want the other so we go -1 HalfYear
#[1] is start for lists
lastHalfYear<-list_of_HalfYears[length(list_of_HalfYears) - 1]
twoYearsAgo<-lastHalfYear-365 - 183 #Double Check Requirements for last "TwoYears" using Last HalfYear
recent_df<-subset(combo, twoYearsAgo < combo$HalfYear & combo$HalfYear <= lastHalfYear ) #We only want 1 total year, so we include Last Half Year, HY represnting "last year", and disclude the next (twoyears ago)
lr_recent<- lmList(Cost ~ HalfYear | LOCATION, data = recent_df)


#pull out the info needed from the linear regression coef(lr))
x<-as.data.frame(coef(lr))
x$`(Intercept)`<-NULL
x$HalfYear[is.na(x$HalfYear)]<-0
names(x)<-c("Slope")
x$LOCATION<-row.names(x)
x$R2<-as.numeric(summary(lr)$r.squared)

#Recent Slope Data
recentData<-as.data.frame(coef(lr_recent))
recentData$`(Intercept)`<-NULL
recentData$HalfYear[is.na(recentData$HalfYear)]<-0
names(recentData)<-c("Recent_Slope")
recentData$LOCATION<-row.names(recentData)


#Cost Criteria
# 1) There has been a charge in the last 2 years
agg_df$CostCriteria1=0
agg_df$CostCriteria1[(agg_df$HalfYear>twoYearsAgo)]<-1
Criteria1=aggregate(CostCriteria1~LOCATION,agg_df,FUN=sum)
Criteria1$CostCriteria1[Criteria1$CostCriteria1>0]=1

# 2) The equipment has cost >$5000 in O&M
agg_df=subset(agg_df, select = c(LOCATION,Cost) )
Criteria2=aggregate(Cost ~ LOCATION, agg_df, FUN = sum)
Criteria2$CostCriteria2=0
Criteria2$CostCriteria2[Criteria2$Cost>5000]=1
Criteria2=subset(Criteria2, select = c(LOCATION,CostCriteria2) )


#Combine Criteria 1 & 2 
Criteria=merge(Criteria1,Criteria2,by="LOCATION")
Criteria$Criteria3=0                    
Criteria$Criteria3[(Criteria$CostCriteria1==1)&(Criteria$CostCriteria2==1)]=1   #If 1 and 2 are present, set C3 as 1
Criteria=subset(Criteria, select = c(LOCATION,Criteria3) )       #Put the lr results and C3 together
results_of_lr=merge(x,Criteria,by="LOCATION")
results_of_lr=merge(results_of_lr,recentData,by="LOCATION")


# 3) Rank the LOCATIONS
results_of_lr$Criteria3[results_of_lr$Slope<0]=0                   #Negative slope = no worries
results_of_lr$Criteria3[results_of_lr$Recent_Slope<0]=0                   #If we have a down slope recently, we do not consider it
results_of_lr=  results_of_lr[with(results_of_lr, order(-R2)), ]          #Order by descending R2 value
row.names(results_of_lr) <- NULL                                          #remove names
results_of_lr$Rank=row.names(results_of_lr)                               #move names to rank
results_of_lr$Rank[results_of_lr$Criteria3<1]=nrow(results_of_lr)+1       #if criterea is lower than 1, we then move it down in rank
results_of_lr$Rank=as.numeric(results_of_lr$Rank)                         #numeric conversion 
results_of_lr$Rank[results_of_lr$Slope<0]=results_of_lr$Rank[results_of_lr$Slope<0]+1   #if slop is negative then we move down rank
results_of_lr=  results_of_lr[with(results_of_lr, order(Rank,-R2)), ]                   #dual order b/t rank # and then R^2
row.names(results_of_lr) <- NULL        #remove names, making it default to "sequential"
results_of_lr$Rank=row.names(results_of_lr) #post sort, we just assign the "automatic names" as rank for selection; update rank

#pull out equipment name
results_of_lr$Equpiment<-0

for (i in 1:nrow(results_of_lr)){
  x<-query_data[(query_data$LOCATION == results_of_lr$LOCATION[i]),"EquipmentProblem"][1]
  x<-paste(unlist(regmatches(x, gregexpr(":.*:", x, perl = TRUE))), collapse = " ")
  results_of_lr$Equpiment[i]<-substr(x,2,nchar(x)-1)
}

results_of_lr=subset(results_of_lr, select = c(Rank,LOCATION,Equpiment) )
rm(list=setdiff(ls(), c("results_of_lr","query_data")))
start.time=Sys.time()
write.csv(results_of_lr, "IncreasingEquipmentCostsRank.csv", row.names=FALSE) #like 2 seconds baby
end.time=Sys.time()
dataProcess.time=end.time-start.time #Again the time-time thing don't really work but my estmiate says says 80~ seconds