import pandas as pd
import geopandas as gpd

parking_gdf = gpd.read_file(r'Inputs/data/2025_Parking_Lots.shp')
parking_s_gdf = gpd.read_file(r'Inputs/data/2025_ParkingParcels.shp') 

parking_gdf.columns
parking_s_gdf.columns
parking_gdf['Map_park']
X_gdf = parking_gdf[parking_gdf['FID_1']==12]
demand = X_gdf[['FID_1', 'RESTRICT', 'Map_park']]
demand[demand['RESTRICT']==1]


supply = parking_s_gdf[['LOT_UID', 'RESTRICT']]

supply[supply['LOT_UID']==244]
supply[supply['RESTRICT']==1]
supply['RESTRICT'].value_counts()
parking_gdf.loc[parking_gdf['FID_1'].isin([48, 49]), 'RESTRICT'] = 7
parking_gdf.loc[parking_gdf['FID_1'].isin([12]), 'RESTRICT'] = 3
parking_gdf.loc[parking_gdf['FID_1'].isin([48, 49]), 'Map_park'] = 1
parking_gdf.loc[parking_gdf['FID_1'].isin([48, 49]), ['FID_1', 'RESTRICT', 'Map_park']]
parking_gdf.loc[parking_gdf['FID_1'].isin([12]), ['FID_1', 'RESTRICT', 'Map_park']]
parking_gdf.to_file(r'Inputs/data/2025_Parking_Lots.shp')
parking_gdf.to_csv(r'Inputs/data/2025_Parking_Lots.csv', index=False)

parking_gdf['privatelot'].value_counts()