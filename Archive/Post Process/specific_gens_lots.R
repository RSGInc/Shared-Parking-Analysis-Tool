#Author: RSG. Aaron Lee
#Date: July 2021
#version 1.0
#This script analyzes the timeseries data for specific parking generators and the occupants of specific lots. 

#Each of the following code pieces analzyes a specific lot or generator ID for the specific scenario of interest. 



#### Get demand info for one or more generators. the 74 is the gen id
gen_demand = demand %>%
  filter(GEN_UID %in% c(74) & Hour==the_hour & Day==the_day & Month == the_month)



#### Get demand info for one or more lots. enter the lot ID
lot_demand = demand %>%
  filter(LOT_UID %in% c(14) & Hour==the_hour & Day==the_day & Month == the_month)



#### Get demand info for one or more lots
lot_demand = demand %>%
  filter(LOT_UID %in% c(66) & Hour==the_hour & Day==the_day & Month == the_month)




#### Get demand info for one or more lots
lot_demand = demand %>%
  filter(LOT_UID %in% c(51,40,70) & Hour==the_hour & Day==the_day & Month == the_month)




### LOTS with high demand ratio

high_demand = d2 %>%
  select(LOT_UID,SPACE_TOT,lot_demand,demand_ratio) %>%
  unique() %>%
  arrange(desc(demand_ratio))



high_demand = d2 %>%
  group_by(LOT_UID,RESTRICT,SPACE_TOT,lot_demand,demand_ratio) %>%
  summarize(demand=sum(demand)) %>%
  arrange(desc(demand_ratio))

high_demand


