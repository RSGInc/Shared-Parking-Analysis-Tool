'''
Creates factors.p, a pickling of the factors dataframe
The factors dataframe contains every combination of factors related to 
shared parking.

@author: David Grover, PE; RSG

For ArcMap, which uses pandas 0.18.1
for later versions of pandas (e.g. ArcGIS Pro), change
pd.read_excel(...,sheetname= => sheet_name=
df.to_excel() doesn't work, not needed for tool, uncomment for later versions

'''

import pandas as pd
import pickle
import arcpy
import os

#############################################
# GET DATA
#############################################

#datapath = r'C:\Projects\VT\CCRCP\19057 - Williston Mixed Use Parking Study\5_GIS\data'.replace('\\','/')
#filename = 'SharedParkingFactors.xlsx'

#datapath = arcpy.GetParameterAsText(0)
filename = arcpy.GetParameterAsText(0)
datapath = os.path.dirname(filename)

landUse_sheetname = 'LandUse'
LUC = 'LUC' # heading name of Land Use Code 
monthly_sheetname = 'Monthly'
TOD_sheetname = 'TOD'

# ---------------
# Land Uses
# ---------------
#demand_data = pd.read_excel(filename,
#                            sheetname=landUse_sheetname,index_col=None,
#                            header=0)
#arcpy.AddMessage('There are {0} rows'.format(len(demand_data.loc[:,'LUC'])))
#
#assert 0
# get data from excel file
# only use rows that have a land use code
demand_data = pd.read_excel(filename,
                            sheetname=landUse_sheetname,index_col=None,
                            header=0).dropna(subset = [LUC])
demand_data[LUC] = demand_data[LUC].astype(int)

# -------------------
# Adjustment Factors
# -------------------

# get monthly adjustment factors from excel file
monthly_sheetname = 'Monthly'
month_adj_all = pd.read_excel(filename,
                              sheetname=monthly_sheetname,index_col=None,
                              header=0).dropna(subset = [LUC])
month_adj_all[LUC] = month_adj_all[LUC].astype(int)

# get time of day adjustment factors from excel file
tod_adj_all = pd.read_excel(filename,
                            sheetname=TOD_sheetname,index_col=None,
                            header=0).dropna(subset = [LUC])

#tod_adj_all = pd.read_excel(filename,
#                            sheetname=TOD_sheetname)
#arcpy.AddMessage(pd.__version__)
#arcpy.AddMessage(tod_adj_all.columns)
tod_adj_all[LUC] = tod_adj_all[LUC].astype(int)

#arcpy.AddMessage(month_adj_all.columns)
#assert 0

#%%##########################################
# GATHER FACTORS
#############################################

# -------------------
# get dimensions
# -------------------

# extract month and hours names from data
n_hours = 19
n_months = 13
months = list(month_adj_all.columns)[n_months*-1:]
hours = list(tod_adj_all.columns)[n_hours*-1:]

# extract land use codes from data
luc_nums = list(set(demand_data.loc[:,LUC]))
luc_nums.sort()

# extract user names from data, make it string and not unicode
users = [str(u) for u in set(demand_data.loc[:,'User'])]
users.sort()

# extract day names from data, make it string and not unicode
days = [str(u) for u in set(tod_adj_all.loc[:,'Day'])]
days.sort()

# -------------------
# Write adjustment df
# -------------------

# preallocate the factors dataframe
factor_index = [(lu,u,d,m,h) for lu in luc_nums for u in users for d in days for m in months for h in hours]
factor_index = pd.MultiIndex.from_tuples(tuples=factor_index,names=['land use','user','day','month','time'])

factors_df = pd.DataFrame(columns = ['month','hour','factor'],index=factor_index)

for land_use in luc_nums:
    for day in days:
        
        
        ToD_factors = tod_adj_all.loc[(tod_adj_all[LUC]==land_use) & (tod_adj_all['Day']==day)]
        
        Month_factors = month_adj_all[month_adj_all[LUC]==land_use]
        # check if there are mulitple days in the month factor data for this land use        
        if len(set(Month_factors.Day)) > 1:
            Month_factors = Month_factors.loc[Month_factors.Day == day]
        
        # extract user names from data, make it string and not unicode
        users1 = set(ToD_factors.loc[:,'User'])
        users2 = set(Month_factors.loc[:,'User'])
        users  = [str(u) for u in users1.union(users2)]
        users.sort()
        
        for user in users:
            ToD_factors = tod_adj_all.loc[(tod_adj_all[LUC]==land_use) & 
                                          (tod_adj_all['Day']==day) &
                                          (tod_adj_all['User']==user)]
            
            Month_factors = month_adj_all[(month_adj_all[LUC]==land_use) &
                                          (month_adj_all['User']==user)]
            
            # check if there are mulitple days in the month factor data for this land use        
            if len(set(Month_factors.Day)) > 1:
                Month_factors = Month_factors.loc[Month_factors.Day == day]            
            
            for month in months:
                if month in ToD_factors.Month:
                    ToD_factors_month = ToD_factors.loc[ToD_factors.Month == month] 
                else:
                    ToD_factors_month = ToD_factors.loc[ToD_factors.Month == 'Typical']
                
                for hour in hours:
                    month_factor = Month_factors.loc[:,month].iloc[0]
                    hour_factor = ToD_factors_month.loc[:,hour].iloc[0]
                    final_factor = month_factor * hour_factor
                    
                    current_factors = pd.Series(data = [month_factor,
                                                        hour_factor,
                                                        final_factor],
                                                index = ['month','hour','factor'])
                    factors_df.loc[(land_use,user,day,month,hour)] = current_factors
                    
# remove cells with no valid combinations
# e.g. user = resident, landuse = retail
factors_df = factors_df.dropna(subset = ['factor'])

# save the factors as a pickle file for import into arcmap
factors_filename = 'factors.p'
path_file = '/'.join([datapath,factors_filename])
pickle.dump(factors_df,open(path_file,"wb"))


#filename = 'Adjustment Factors.xlsx'
#factors_df.to_excel(filename)


#%%##########################################
# TO REFERENCE A FACTOR
#############################################

'''

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
'''






