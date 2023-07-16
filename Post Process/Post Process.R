#Author: RSG.
#Date: July 2021
#version 1.0
#This script extracts data from the analysis completed in the python scripting Shared Parking analysis


#Step 1: Load Packages

rm(list = ls())

library(tidyverse)
library(readxl)
library(openxlsx)
library(sp)
library(rgdal)

#Step 2: Define the Project. The project name is used to manage the source of files.
#this is used to chose the file locations below
#project = "winooski_ave", "winooski_city"
#project = "winooski_city"
project = "winooski_ave"

#Step 3: Inputs to select the analysis data
# Scenario output folder Name (point this to the output folder from the python cnfg.yaml script)
scen_name = "output"

# Demand and Adjustments File Used in Scenario. This is the Shared Parking Excel data file
factors_used = "Parking Demand and Adjustments3"

# Generator (Demand) Shapefile used (in github parent folder  /data )
# Referred to as the demand_shapefile in the CNFG.yaml
#demand_shp = "Demand_small2"
#demand_shp = "WinCity_Calibratedbased"
#demand_shp = "WinCity_NearTerm_Sc1"
#demand_shp = "Winooski_Generators"
demand_shp = "Winooski_Generators"

# Parking (Supply) Shapefile Used (in github parent folder  /data )
# Referred to as the supply_shapefile in the CNFG.yaml
#supply_shp = "Supply_Small2"
#supply_shp = "WinCity_BaseCalibration_Supply"
#supply_shp = "WinCity_NearTerm_Sc1_parking"
supply_shp = "Winooski_Parking"
#supply_shp = "WinCity_Calibratedbased"



##### Data directories for each project
### model_dir = parent directory for python script and where the CONFG.yaml is located.
### dir = directory for desired outputs or any non-python related inputs (likely not needed anymore)

##### WIN CITY #####
if(project == "winooski_city"){

  #dir = "C:/Users/aaron.lee/OneDrive - Resource Systems Group, Inc/20180-WinCityPMP/tasks/ParkModel/New Model Results/Calibration Comparison and Processing"
  model_dir = "C:/GitHub/shared_parking/WinCityTests/tests/base"

}
##### WIN AVE #####
if(project == "winooski_ave"){
  
  #dir = "C:/GitHub/shared_parking/WinAveTests/DemandOut"
  model_dir = "C:/Github/shared_parking/WinAveTests/future_3"
  
}
#may note need this step
## input and output directory names for dir (not python model inputs/outputs
##inputs = paste(dir,"Inputs",sep="/")
#outputs = paste(dir,"baseoutput",sep="/")



#Step 4: Reading the Data
# ################# #
##### READ DATA #####
# ################# #

# python outputs for the scenario
results = read_csv(paste(model_dir,scen_name,"timeseries.csv",sep="\\"))
demand = read_csv(paste(model_dir,scen_name,"demand.csv",sep="\\"))
factors = read_csv(paste(model_dir,scen_name,"factors.csv",sep="\\"))

### Parking and categories and generator list
# reads shapefiles from the python data directory. these are the inputs that were used for the model run. The file should find the above referenced directories for data.
source("Source/read_shapefiles.R")


#Step 5: Analysis of the Parking Data
# #################################### #
##### ANALYSIS and OUTPUT CREATION #####
# #################################### # 


### Day and Time to use for analysis
the_month = "Sep"
the_day = "Weekday"
the_hour = 14


### checks capacity vs. demand at high level
source("Source/constraint check.R")

### prints summary
constraint_check_summary


### more detailed check of demand and capacity. needed for plot below and demand/capacity outputs
source("Source/demand check.R")

## plots demand vs. capacity
ggplot(data = compare2 %>% filter(Day==the_day),aes(Hour,demand,color=factor(Type))) +
  geom_line() +
  ggtitle(paste0(the_month," - ",the_day))

#remove this line
### Counts analysis: creates Weekday and Weekday count compare outputs
#source("Source/counts_analysis.R")


### Capacity vs. Demand for desired hour: Creates Capacity vs. Demand output
# d2 is created in demand check and is total demand for hour/day/month combo
cap_vs_demand = d2 %>%
  left_join(parking %>% select(LOT_UID,LOT_NAME)) %>%
  group_by(LOT_UID,LOT_NAME,Category) %>%
  summarise(capacity = mean(SPACE_TOT)
            ,demand = sum(demand)
            ,overcapacity =ifelse(demand>capacity,demand-capacity,0)) %>%
  arrange(desc(overcapacity))


#### ON STREET SHARE for desired output: Creates on-street share output
## select the Land Use code of interest. Use the Land Use codes in the Parking Demand and Adjustments Excel file.
on_street = demand %>%
  left_join(park_info) %>%
  mutate(LU_Type = ifelse(LUC %in% c(50,51),"Residential_Demand","Commercial_Demand")) %>%
  filter(Day==the_day,Month==the_month) %>%
  group_by(Hour,LU_Type) %>%
  summarize(On_Street = sum(demand*(Category %in% c("On Street","on street")))
            ,total=sum(demand)
            ,On_street_share = sum(demand*(Category %in% c("On Street","on street")))/sum(demand)) %>%
  pivot_wider(names_from=LU_Type,values_from=c(On_Street,total,On_street_share))


#Step 6: Writing to Excel for analysis and visualization
# ##################### #
##### WRITE TO XLSX #####
# ##################### #

# will write an xlsx file with all check outputs to project outputs folder with name including scenario, day and hour

output = list(timeseries= results
              ,parking_formatted = parking
#              ,Weekday_Count = wd_compare_output
#              ,Weekend_Count = we_compare_output
              ,Unconstrained_Demand = demand_check_output
              ,Capacity_and_Demand = constraint_check_output
              ,Capacity_by_lot = cap_vs_demand
              ,On_Street_Share = on_street)

#write.xlsx(output,paste0(output,"\\",scen_name,"_checks_",the_day,the_hour,".xlsx"),overwrite=TRUE)
write.xlsx(output, file = paste0(output,"\\",scen_name,"_checks_",the_day,the_hour,".xlsx"),overwrite=TRUE)


# write.csv(parking,paste0(outputs,"/parking.csv"),row.names=FALSE)
