# Script for updating visualization.xslx tabs
library(tidyverse)
library(openxlsx)

## This script will clear current data in visualization.xlsx tabs:
### timeseries and parking_formatted,
### with data from the appropriate CSV files.


# Adjust these folder directories where necessary to get correct file
temp <- dirname(getwd())

timeseries <- read.csv(paste(model_dir,scen_name, "timeseries.csv", sep="/"))
  

# Parking shapefile already processed
parking2 <- parking %>% data.frame()

# Load workbook
viz <- loadWorkbook("Post Process/visualization.xlsx")

writeData(viz, sheet = "timeseries", x=timeseries)
writeData(viz, sheet = "parking_formatted", x=parking2)


# Save workbook
saveWorkbook(viz, scen_name,"visualization.xlsx", overwrite = T)
