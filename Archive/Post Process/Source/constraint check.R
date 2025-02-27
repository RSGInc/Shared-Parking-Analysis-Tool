


# ################################## #
##### SCRIPT TO TEST CONSTRAINTS #####
# ################################## #


### PACKAGES and SCRIPTS ###


### extra data

#demand = read_csv(paste(model_dir,scen_name,"demand.csv",sep="/"))
#generators = read_rds(paste0(inputs,"/generator_list.rds"))





### park info to merge
park_info = parking %>%
  select(LOT_UID,RESTRICT,Street,Category)


### demand for sept at 13h
d2 = demand %>%
  filter(Month==the_month,Day==the_day ,Hour %in% the_hour) %>%
  left_join(park_info) %>%
  mutate(LU_Type = ifelse(LUC %in% c(50,51),"Residential_Demand","Commercial_Demand")) 

demand_sum = d2 %>%
  group_by(LU_Type,Category) %>%
  summarise(demand = sum(demand)) %>%
  pivot_wider(names_from = LU_Type,values_from = demand)



parking_sum = parking %>%
  group_by(Category) %>%
  summarise(capacity = sum(SPACE_TOT))


### this is a key table
constraint_check_summary = parking_sum %>%
  left_join(demand_sum)



demand_sum = d2 %>%
  group_by(LU_Type,Category,Street) %>%
  summarise(demand = sum(demand)) %>%
  pivot_wider(names_from = c(LU_Type,Category),values_from = demand)



parking_sum = parking %>%
  group_by(Category,Street) %>%
  summarise(capacity = sum(SPACE_TOT)) %>%
  pivot_wider(names_from = (Category),values_from=capacity,names_prefix="capacity_")


### this is a key table
constraint_check_output = parking_sum %>%
  left_join(demand_sum)
