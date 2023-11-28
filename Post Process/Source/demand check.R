


# ################################### #
##### SCRIPT TO TEST TOTAL DEMAND #####
# ################################### #


### PACKAGES and SCRIPTS ###

### Libraries
require(readxl)
require(tidyverse)
library(rgdal)
library(ggplot2)

### Source scripts ###



generators2 = generators %>%
  left_join(factors, relationship = "many-to-many") %>%
  mutate(demand = SIZE * factor)


# ############### #
##### ANALYZE #####
# ############### #


dmd = demand %>%
  filter(Month==the_month) %>%
  group_by(Day,Hour) %>%
  summarise(demand = sum(demand))

gens = generators2 %>%
  filter(Month==the_month) %>%
  group_by(Day,Hour) %>%
  summarise(demand = sum(demand))

rlts = results %>%
  filter(Month==the_month) %>%
  group_by(Day,Hour) %>%
  summarise(demand = sum(demand))

compare = dmd %>%
  left_join(rlts, by=c("Day","Hour"),suffix=c("_unconstrained","_model")) %>%
  mutate(overcapacity = ifelse(demand_unconstrained>demand_model,demand_unconstrained-demand_model,0))

capacity = expand.grid(Day = c("Weekday","Weekend"),Hour = unique(compare$Hour)) %>%
  mutate(capacity=sum(parking$SPACE_TOT)
         ,onstreet_cap= sum(parking$SPACE_TOT*(parking$RESTRICT==0))
         ,res_cap = sum(parking$SPACE_TOT*(parking$RESTRICT==1))
         ,comm_cap = sum(parking$SPACE_TOT*(parking$RESTRICT==2))) %>%
  pivot_longer(names_to = "Type",cols = c(3:6),values_to = "demand")

compare2 = rbind(dmd %>% mutate(Type="Unconstrained"),rlts %>% mutate(Type="Modeled"))



ggplot(data = compare,aes(Hour,demand_unconstrained,color=factor(Day))) +
  geom_line() +
  geom_abline(slope=0,intercept=sum(parking$SPACE_TOT))

ggplot(data = compare,aes(Hour,demand_model,color=factor(Day))) +
  geom_line() +
  geom_abline(slope=0,intercept=sum(parking$SPACE_TOT))

ggplot(data = compare,aes(demand_unconstrained,demand_model,color=factor(Day))) +
  geom_point() +
  geom_abline(slope=1,intercept=0)



sum(compare$demand_model)           ## 59311.07
sum(compare$demand_unconstrained)   ## 59311.07

##sum(parking$SPACE_TOT)
# 4069

parking %>%
  group_by(RESTRICT) %>%
  summarise(sum(SPACE_TOT))


demand_check_output = compare

rm(rlts)
rm(dmd)







