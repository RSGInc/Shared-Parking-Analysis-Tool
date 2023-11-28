#Author: RSG.
#Date: July 2023
#version 1.2
#This script extracts data from the analysis completed in the python scripting Shared Parking analysis
# Several steps and folder locations are needed to complete this script. 


#Step 1: Load Packages
# ##################### #
##### LOAD PACKAGES #####
# ##################### #

rm(list = ls())

library(tidyverse)
library(readxl)
library(openxlsx)
library(sp)
library(rgdal)
library(sf)
library(terra)

#Step 2: Define the Project. The project name is used to manage the source of files.
# ###################### #
##### DEFINE PROJECT and Folder Locations #####
# ###################### #

#project = "winooski_ave", "winooski_city", or other folders toggle these for project type
project = "winooski_city"

##### Data directories for each project
### model_dir = parent directory for python script, where output files are stored
### dir = directory for desired outputs or any non-python related inputs (likely not 
### needed anymore), substitute own directory
##### WIN CITY #####
if(project == "winooski_city"){
  
  #dir = "C:\\Shared_Parking\\Calibration Comparison and Processing"
  model_dir = "C:/GitHub/Shared-Parking-Analysis-Tool/"
  
}
##### WIN AVE #####
if(project == "winooski_ave"){
  
  dir = "C:/GitHub/shared_parking/WinAveTests/DemandOut"
  model_dir = "C:/WINCity task/shared_parking/WinAveTests/future_3"
  
}

# Scenario Name (point this to the output folder from the python script)
# only put the name of the folder where the python outputs are stored.
scen_name = "Output/base/baseoutput"

## input and output directory names for the Excel outputs from the python files
#inputs = paste(dir,"Inputs",sep="/")
outputs = paste(model_dir,scen_name,sep="/")

# Demand and Adjustments File Used in Scenario. This is the Shared Parking Excel data file
factors_used = "Parking Demand and Adjustments"

# Name of Parking (Supply) Shapefile Used in the analysis
#supply_shp = "Supply_Small2"
supply_shp = "WinCity_BaseCalibration_Supply"
#supply_shp = "WinCity_NearTerm_Sc1_parking"
#supply_shp = "Winooski_Parking"


# Name of Generator (Demand) Shapefile used in the analysis
#demand_shp = "Demand_small2"
demand_shp = "WinCity_Calibratedbased"
#demand_shp = "WinCity_NearTerm_Sc1"
#demand_shp = "Winooski_Generators"



#Step 3: Reading the Data for Analysis
# ################# #
##### READ DATA #####
# ################# #

# python outputs for the scenario
results = read_csv(paste(model_dir,scen_name,"timeseries.csv",sep="\\"))
demand = read_csv(paste(model_dir,scen_name,"demand.csv",sep="\\"))
factors = read_csv(paste(model_dir,scen_name,"factors.csv",sep="\\"))

### Parking and categories and generator list
# reads shapefiles from the python data directory. 
# these are the inputs that were used for the model run. 
# The file should find the above referenced directories for data.
source("Post Process/Source/read_shapefiles.R")


#Step 4: Analysis of the Parking Data
# #################################### #
##### ANALYSIS and OUTPUT CREATION #####
# #################################### # 


### Day and Time to use for analysis
the_month = "Sep"
the_day = "Weekday"
the_hour = 14

### checks capacity vs. demand at high level
source("Post Process/Source/constraint check.R")

### prints summary
constraint_check_summary

### more detailed check of demand and capacity. needed for plot below and demand/capacity outputs
source("Post Process/Source/demand check.R")

## plots demand vs. capacity
ggplot(data = compare2 %>% filter(Day==the_day),aes(Hour,demand,color=factor(Type))) +
  geom_line() +
  ggtitle(paste0(the_month," - ",the_day))

########################################
# Count Analysis - unused at this time. 
########################################

### Counts analysis: creates Weekday and Weekend count compare outputs
#if(project == "winooski_city"){
#  source(paste(dir,"Source/win_city_counts.R", sep="/"))
#}

#if(project == "winooski_ave"){
#  source(paste(dir,"Source/win_ave_counts.R"))
#}

#source("Post Process/Source/counts_analysis.R")


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
## select the Land Use code of interest. 
## Use the Land Use codes in the Parking Demand and Adjustments Excel file.
on_street = demand %>%
  left_join(park_info) %>%
  mutate(LU_Type = ifelse(LUC %in% c(50,51),"Residential_Demand","Commercial_Demand")) %>%
  filter(Day==the_day,Month==the_month) %>%
  group_by(Hour,LU_Type) %>%
  summarize(On_Street = sum(demand*(Category %in% c("On Street","on street")))
            ,total=sum(demand)
            ,On_street_share = sum(demand*(Category %in% c("On Street","on street")))/sum(demand)) %>%
  pivot_wider(names_from=LU_Type,values_from=c(On_Street,total,On_street_share))



########################################################################################
#Step 5: Writing to Excel for analysis and visualization for specific day and time.
# ##################### #
# will write an xlsx file with all check outputs to project outputs folder with 
# name including scenario, day and hour

output = list(timeseries= results
              ,parking_formatted = parking
#              ,Weekday_Count = wd_compare_output
#              ,Weekend_Count = we_compare_output
              ,Unconstrained_Demand = demand_check_output
              ,Capacity_and_Demand = constraint_check_output
              ,Capacity_by_lot = cap_vs_demand
              ,On_Street_Share = on_street)

write.xlsx(output,paste0(model_dir,scen_name,"_checks_",the_day,the_hour,".xlsx"),overwrite=TRUE)


##############################################################################
# Step 6: Full Analysis Updating the visualization file with new parking and timeseries info
# Note: the Visualization Excel file will be overwritten.
##############################################################################
### Adjust these model folder/names as necessary to create a path to the model and output
#model_folder="WinCityTests"  #### old variable  delete?
#output_folder <- "/../Output/base/baseoutput/"    #### old variable. delete?

source("Post Process/Source/save_visualization.R")

# write.csv(parking,paste0(outputs,"/parking.csv"),row.names=FALSE)
