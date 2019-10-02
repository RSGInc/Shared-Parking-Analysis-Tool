# -*- coding: utf-8 -*-
"""
Created on Fri May 24 10:12:13 2019

generate_parking_demand.py

@author: david.grover


reference a factor:
     factors_df.loc[(land_use,user,day,month,hour),factor_type]
     
     variable values:
         land_use:
             [1, 2, 3, 4, 5]
         user:
             ['Employee', 'Visitor']
         day:
             ['Weekday', 'Weekend']
         month:
             ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','Late Dec']
             
     e.g.:
         land_use = 5 # office space, may change with new ULI
         user = 'Employee'
         day = 'Weekday'
         month = 'Jun'
         hour = 16 # 4pm
         factor_type = 'factor' # month * day
         factors_df.loc[(land_use,user,day,month,hour),factor_type]
     
    e.g.
         get total factors for all time/user combos for land use 'land_use'
         factors_df.loc[(land_use,slice(None),slice(None),slice(None),slice(None)),'factor']
         
For ArcMap, which uses pandas 0.18.1
for later versions of pandas (e.g. ArcGIS Pro), change
pd.read_excel(...,sheetname= => sheet_name=

"""

import pandas as pd
import pickle
import time
import arcpy
import os

#datapath = r'C:\Projects\VT\CCRCP\19057 - Williston Mixed Use Parking Study\5_GIS\data'.replace('\\','/')

# ------------------
# Parking Lots
# ------------------

parking_lot_filename = arcpy.GetParameterAsText(0)                                      #'Parking Lots.xlsx'
lot_sheet_name = arcpy.GetParameterAsText(1)                                     #'Sheet1'
lot_ind_col = arcpy.GetParameterAsText(2)                                       #'Location ID'

#lots = pd.read_excel(parking_lot_filename, sheetname = sheet_name)
#arcpy.AddMessage(lots.columns)
#assert 0

lots = pd.read_excel(parking_lot_filename, sheetname = lot_sheet_name, 
                     header=1, index_col=lot_ind_col)   #'/'.join([datapath,filename])
#lots.SpTest = int(arcpy.GetParameterAsText(3))                              #40 # change spaces available for testing

# ------------------
# Adjustment Factors
# ------------------

factor_filename = arcpy.GetParameterAsText(9)                                      #'factors.p'
factors_df = pd.read_pickle(factor_filename)                                       # uPDATED FOR PYTHON 2.7
##path_file = '/'.join([datapath,filename])
##factors_df = pickle.load(open(filename,"rb"))   #path_file

# ------------------
# Parking Generators
# ------------------

generator_filename = arcpy.GetParameterAsText(3)                                      #'Land Uses.xlsx'
gen_sheet_name = arcpy.GetParameterAsText(4)                                     #'Sheet1'
gen_ind_col = arcpy.GetParameterAsText(5)                                       #'Location'

generators = pd.read_excel(generator_filename ,sheetname=gen_sheet_name, 
                           header=1, index_col=gen_ind_col) #'/'.join([datapath,filename])
generators['lots'] = 0 # preallocate column
generators['lots'] = generators['lots'].astype(object) # make cells in col accept lists

## CHANGE THIS TO BE READ IN FROM EXCEL FILE, ALL COLUMNS AFTER 'SIZE'
#lot_cols = ['Parking_1','Parking_2','Parking_3','Parking_4','Parking_5','Parking_6']
#
# get list of lots for each land use


for i in generators.index:
    a = generators.loc[i,'ParkingLots']
    if not (isinstance(a, int) or isinstance(a, float)):
        b = [int(x) for x in a.split(';')]
    else:
        b = [int(a)]
#    a = generators.loc[i,lot_cols].tolist()
#    b = [int(x) for x in a if not pd.isnull(x)]
    generators.at[i,'lots'] = b


# ---------------
# Demand
# ---------------

demand_filename = arcpy.GetParameterAsText(6)                                      #'Parking Demand and Adjustments.xlsx' 
demand_sheet_name = arcpy.GetParameterAsText(7)                                     #'Demand by Land Use'
# Added user input for land use field name
landuse_col = arcpy.GetParameterAsText(8)

# get data from excel file
# only use rows that have a land use code
demand_data = pd.read_excel(demand_filename, sheetname = demand_sheet_name, 
                            index_col=None).dropna(subset = [landuse_col])   #'/'.join([datapath,filename]) #'ULI_LU'
demand_data[landuse_col] = demand_data[landuse_col].astype(int)         #demand_data.ULI_LU = demand_data.ULI_LU.astype(int)

# dictionary of demands for each generator
gen_demands = dict()

# get list of dimensions

days = set(factors_df.index.get_level_values('day'))
months = set(factors_df.index.get_level_values('month'))
hours = set(factors_df.index.get_level_values('time'))

gen_demand_index = [(d,m,h) for d in days for m in months for h in hours]
gen_demand_index = pd.MultiIndex.from_tuples(tuples=gen_demand_index,names=['day','month','time'])

# factors_df.loc[(land_use,user,day,month,hour),factor_type]

start_time = time.time()

for generator in generators.index:
    
    # get info about this generator
    size = generators.loc[generator,'Size']
    land_use = generators.loc[generator,'LUC']
    
    # get list of users
    users = set(demand_data.loc[demand_data.loc[:,'LUC'] == land_use,'User'])
    
    # preallocate this generator's demands
    gen_demands[generator] = pd.Series(data = 0,index=gen_demand_index)
    
#    for u in users:
#        demand[u] = demand_data.loc[(demand_data.ULI_LU == land_use) & 
#              (demand_data.User == u),d]
    for (d,m,h) in gen_demand_index:
#        factor = dict()
#        demand = dict()        

#        d = 'Weekend'
#        m = 'Dec'
#        h = 14
#                
        for u in users:
            

            demand = demand_data.loc[(demand_data.LUC == land_use) & 
                  (demand_data.User == u),d].iloc[0]
            factor = factors_df.loc[(land_use,u,d,m,h),'factor']
            
            gen_demands[generator].loc[(d,m,h)] += demand * factor * size
        
        
end_time = time.time()
run_time = end_time - start_time

arcpy.AddMessage('Defined demand in {0:.1f} seconds.'.format(run_time))

## example - Yankee Candle
#generator = 11067
#gen_demands[generator].loc[('Weekend','Dec',slice(None))] # demand in December
#generators.loc[generator,:] # generator characteristics
#generators.loc[generator,'lots']
#
#generators.loc[:,['lots','Name']]


# ------------------
# Distribute Parking
# ------------------

#d = 'Weekend'
#m = 'Dec'
#h = 14
#generator = 10537
#lot = 434

# define constants
PARK_EACH_TIME = .20 # decimal amount of total to park each iteration 0.05 = 5%

# preallocate dimension-dependent variables
gen_demands_met = dict()
for generator in generators.index:
    gen_demands_met[generator] = pd.Series(data = 0,index=gen_demand_index)
    
lots_filled = dict()
for lot in lots.index:
    lots_filled[lot] = pd.Series(data = 0,index=gen_demand_index)
    
demand_exceeds_supply = dict()
for generator in generators.index:
    demand_exceeds_supply[generator] = pd.Series(data = False,index=gen_demand_index)

start_time = time.time()

for (d,m,h) in gen_demand_index:
    unmet = True # is there unmet demand for spaces?
    while unmet: # there is still some unmet demand
        unmet = False # assume that all of the demand will be met this iteration
        for generator in generators.index:
            if demand_exceeds_supply[generator].loc[(d,m,h)]: # if this gen's lots are alreay full
                continue # don't bother with the rest
            g_lots = generators.loc[generator,'lots']
            total_demand_left = gen_demands[generator].loc[(d,m,h)] - gen_demands_met[generator].loc[(d,m,h)]
            max_fill_demand = PARK_EACH_TIME * gen_demands[generator].loc[(d,m,h)]
            demand_left = min(max_fill_demand,total_demand_left)
            
            fill_lot = 0 # put demand in this lot
            while demand_left and len(g_lots)>fill_lot:
                lot = g_lots[fill_lot]
                supply_left = lots.loc[lot,'Spaces'] - lots_filled[lot].loc[(d,m,h)]
                if supply_left:
                    fill_spaces = min(supply_left,demand_left)
                    demand_left -= fill_spaces
                    lots_filled[lot].loc[(d,m,h)] += fill_spaces
                    gen_demands_met[generator].loc[(d,m,h)] += fill_spaces
                fill_lot += 1
            
            # check if there is supply left
            fill_lot = 0 # put demand in this lot
            supply_left = 0
            while not supply_left and len(g_lots)>fill_lot:
                lot = g_lots[fill_lot]
                supply_left += lots.loc[lot,'Spaces'] - lots_filled[lot].loc[(d,m,h)]
                fill_lot += 1
            if (not supply_left
                and gen_demands[generator].loc[(d,m,h)] > gen_demands_met[generator].loc[(d,m,h)]): # this gen still needs spaces
                demand_exceeds_supply[generator].loc[(d,m,h)] = True
            
            if (not unmet # this is the first occurance of unmet demand
                and gen_demands[generator].loc[(d,m,h)] > gen_demands_met[generator].loc[(d,m,h)] # this gen still needs spaces
                and not demand_exceeds_supply[generator].loc[(d,m,h)]): # this gen still has lots to fill
                 
                unmet = True # do another iteration

end_time = time.time()
run_time = end_time - start_time
arcpy.AddMessage('Distributed demand in {0:.1f} seconds.'.format(run_time))
#print('Distributed demand in',run_time, 'seconds.')


###################
# GIS Table
###################

months = {
        'Apr' : '04',
        'Aug' : '08',
        'Dec' : '12',
        'Feb' : '02',
        'Jan' : '01',
        'Jul' : '07',
        'Jun' : '06',
        'Late Dec' : '12',
        'Mar' : '03',
        'May' : '05',
        'Nov' : '11',
        'Oct' : '10',
        'Sep' : '09'}

days = {'Weekday':'01', 'Weekend':'05'}


gis_table_index = [[int(l),d,m,int(h)] for l in lots.index 
                    for (d,m,h) in gen_demand_index.tolist()]
gis_table_df = pd.DataFrame(data = 0, index = range(len(gis_table_index)), 
                            columns = [lot_ind_col,'spcsLeft',
                                       'pcntFull','timeStmp'])
gis_table_df.index.name = 'ObjectID'

start_time = time.time()

row = 0
for (lot,d,m,h) in gis_table_index:
    percent_full = lots_filled[lot].loc[(d,m,h)] / float(lots.loc[lot,'Spaces'])
    # timestamp format is YYYYMMDDhhmmss
    # code weekdays as 1, weekends as 5
    # late December: weekday = 11, weekend = 15
    if m != 'Late Dec':
        timestamp = '2019' + months[m] + days[d] +'{0:0>2}0000'.format(h)
    else:
        if d == 'Weekday':
            timestamp = '2019' + months[m] + '11' +'{0:0>2}0000'.format(h)
        elif d == 'Weekend':
            timestamp = '2019' + months[m] + '15' +'{0:0>2}0000'.format(h)
        else:
            arcpy.AddMessage('day is not defined correctly')
            raise
    gis_table_df.loc[row,[lot_ind_col,'spcsLeft','pcntFull','timeStmp']] = [
            lot, lots.loc[lot,'Spaces']-lots_filled[lot].loc[(d,m,h)],percent_full,timestamp]
    row += 1

end_time = time.time()
run_time = end_time - start_time
arcpy.AddMessage('Created table in {0:f} seconds.'.format(run_time))



datapath = arcpy.GetParameterAsText(10)                                    #'/'.join([datapath,filename])

# export table to csv
filename = arcpy.GetParameterAsText(11)                                     #'lot_pcntFull_timeseries.csv'
gis_table_df.to_csv(os.path.join(datapath, filename+".csv"))               #('/'.join([path_file,filename]))

# save demand and parking lot as pickle files
create_pickles = arcpy.GetParameterAsText(12)  
if create_pickles:
    demand_filename = 'GenDemand.p'
    filepath = '/'.join([datapath,demand_filename])
    pickle.dump(gen_demands,open(filepath,"wb"))
    ParkingLot_filename = 'ParkingLots.p'
    filepath = '/'.join([datapath,ParkingLot_filename])
    pickle.dump(gis_table_df,open(filepath,"wb"))

'''
# check files
# use this code to query the *.p file created by the tool
import pandas as pd
demand_filename = r'C:\Projects\VT\CCRCP\19057 - Williston Mixed Use Parking Study\5_GIS\Parking Analysis Tools\2_Data\Output Data\GenDemand.p'
gen_demands = pd.read_pickle(demand_filename) 

ParkingLot_filename = r'C:\Projects\VT\CCRCP\19057 - Williston Mixed Use Parking Study\5_GIS\Parking Analysis Tools\2_Data\Output Data\ParkingLots.p'
gis_table_df = pd.read_pickle(ParkingLot_filename) 

print(gen_demands[9997].loc[('Weekday','Dec',slice(None))])
print(gen_demands[10176].loc[('Weekday','Dec',slice(None))])

'''
#%% Write Report File
aggregation_functions = {'spcsLeft': 'sum'}
df_totalSpacesLeft = gis_table_df.groupby(gis_table_df['timeStmp']).aggregate(aggregation_functions)
least_spaces_timestamp = df_totalSpacesLeft['spcsLeft'].idxmin()

year = least_spaces_timestamp[0:4]
month = int(least_spaces_timestamp[4:6])
day = int(least_spaces_timestamp[6:8])
hour = int(least_spaces_timestamp[8:10])

#print('{')
#for k,v in days.items():
#    print '{} : "{}",'.format(int(v),k)
#print('}')

month_num2Word = {2 : "Feb",
    8 : "August",
    1 : "January",
    12 : "December",
    10 : "October",
    3 : "March",
    9 : "September",
    5 : "May",
    6 : "June",
    7 : "July",
    4 : "April",
    11 : "November"}

day_num2Word ={5 : "Weekend", 1 : "Weekday",}

hour2time = {
        0 : '12:00 Midnight',
        6 : '6:00 AM',
        6 : '6:00 AM',
        7 : '7:00 AM',
        8 : '8:00 AM',
        9 : '9:00 AM',
        10 : '10:00 AM',
        11 : '11:00 AM',
        12 : '12:00 Noon',
        13 : '1:00 PM',
        14 : '2:00 PM',
        15 : '3:00 PM',
        16 : '4:00 PM',
        17 : '5:00 PM',
        18 : '6:00 PM',
        19 : '7:00 PM',
        20 : '8:00 PM',
        21 : '9:00 PM',
        22 : '10:00 PM',
        23 : '11:00 PM'}
if day > 10:
    month = 'Late December'
else:
    month = month_num2Word[month]
if day%5 == 0:
    day = 'weekend'
else:
    day = 'weekday'
hour = hour2time[hour]

report_file = os.path.join(datapath, filename+"_report.txt")
with open(report_file,'w') as text_file:
    text_file.write(
            'The lowest space availablility occurs at {} on a {} in {}.'.format(
                    hour,day,month))
    text_file.write('\n\n')
    no_unmet_demand = True
    for (d,m,h) in gen_demand_index:
        for generator in generators.index:
            if demand_exceeds_supply[generator].loc[(d,m,h)]:
                notice_str = 'Unmet demand for generator {} on a {} in {} at {}00\n'.format(
                        generator,d,m,h)
                text_file.write(notice_str)
                no_unmet_demand = False
    if no_unmet_demand:
         text_file.write('All demand is met for all generators.')


    
#%%
    
######################
# Over Capacity?
######################

#for (d,m,h) in gen_demand_index:
#    for generator in demand_exceeds_supply.keys():
##    for (d,m,h) in demand_exceeds_supply[generator].index:
#        if demand_exceeds_supply[generator].loc[(d,m,h)]:
#            print('On a {1} in {2} at {3}:00, {0} requires more spaces.'.format(
#                    generators.loc[generator,'Name'],
#                    *[d,m,h]))




#######################
# Junk
#######################
#
#
#
#        demand_exceeds_supply[generator].loc[(d,m,h)]
#
#for lot in lots.index:
#    lots_filled[lot] = pd.Series(data = 0,index=gen_demand_index)
#
#
#
#
#
#
##set([m for (d,m,h) in gen_demand_index.tolist()])
#set([d for (d,m,h) in gen_demand_index.tolist()])
#set([h for (d,m,h) in gen_demand_index.tolist()])
#
####################
## Testing Variables
####################
#for lot in lots.index:
#    print(lot, lots_filled[lot].loc[(d,m,h)])
#
#for generator in generators.index:
#    print( generator, demand_exceeds_supply[generator].loc[(d,m,h)])
#
#generators.loc[10922]
#
#g_index = generators.index
#
#g_index_num = 0
#generator = g_index[g_index_num]
#
#g_index_num += 1
#generator = g_index[g_index_num]
#
#
#
#
#
#g_lots = generators.loc[generator,'lots']
#demand = gen_demands[generator].loc[('Weekend','Dec',15)]
#lot_number = 0
#while demand:
#    park = min(PARK_EACH_TIME,demand)
#    demand -= park
#    lots

#            
#    
#    factors_df.loc[(land_use,u,slice(None),slice(None),slice(None)),'factor']
#            
#    factors_df.loc[(land_use,'Jan'),:]
#    factors_df.loc[(land_use,slice(None),slice(None),slice(None),slice(None)),'factor'].index
#    factors_df.index
#    assert 0
#    users = 1
