## count analysis




### ALL ###

all_counts = database %>%
  subset(Month =="Sep") %>%
  subset(!is.na(mean))

# plot(all_counts$frac_full,all_counts$mean)


### By STREET Weekday

wd_mid = database %>%
  subset(Hour %in% c(11,15,19) & Month==the_month & Day=="Weekday")

wd_compare_output = wd_mid %>%
  filter(Category=="On Street") %>%
  group_by(Street,Hour) %>%
  summarise(Total_Spaces = sum(SPACE_TOT,na.rm=TRUE)
            ,Demand = sum(demand,na.rm=TRUE)
            ,Expected_Demand = sum(mean*SPACE_TOT,na.rm=TRUE)) %>%
  filter(Expected_Demand>0)

wd_compare_output


### By STREET Weekend 

we_am = database %>%
  subset(Hour %in% c(10,17) & Month==the_month & Day=="Weekend")

we_compare_output = we_am %>%
  filter(Category=="On Street") %>%
  group_by(Street,Hour) %>%
  summarise(Total_Spaces = sum(SPACE_TOT,na.rm=TRUE)
            ,Demand = sum(demand,na.rm=TRUE)
            ,Expected_Demand = sum(mean*SPACE_TOT,na.rm=TRUE)) %>%
  filter(Expected_Demand>0)

we_compare_output

### On street vs off street

### weekday mid

test = wd_mid %>%
  group_by(Street,Category,Hour) %>%
  summarise(Pct_Full = sum(demand,na.rm=TRUE)/sum(SPACE_TOT,na.rm=TRUE)) %>%
  pivot_wider(names_from="Category",values_from="Pct_Full")



### Total Demand

total_demand = wd_mid %>%
  group_by(Street,Category,Hour) %>%
  summarise(Demand = sum(demand)) %>%
  pivot_wider(names_from="Category",values_from="Demand")







total_demand = database %>%
  filter(Month==the_month,Day=="Weekday",Hour %in% c(8,13,18)) %>%
  group_by(Category,Time_Period) %>%
  summarise(Demand = sum(demand)) %>%
  pivot_wider(names_from="Category",values_from="Demand")

total_demand

total_demand = database %>%
  filter(Month=="Sep",Day=="Weekday",Hour %in% c(8,13,18)) %>%
  group_by(Street,Category,Time_Period) %>%
  summarise(Demand = sum(demand)) %>%
  pivot_wider(names_from="Category",values_from="Demand")

total_demand
