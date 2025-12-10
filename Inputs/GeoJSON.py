import pandas as pd
import geopandas as gpd


timeseries_df = pd.read_csv('outputs/timeseries.csv')
parking_gdf = gpd.read_file('data/2025_Parking_Lots.shp')

timeseries_gdf = timeseries_df.merge(parking_gdf, on='FID_1')

## convert to GeoDataFrame
timeseries_gdf = gpd.GeoDataFrame(timeseries_gdf, geometry=timeseries_gdf.geometry, crs=parking_gdf.crs)
timeseries_gdf = timeseries_gdf.to_crs(epsg=4326)

#save to GeoJSON
timeseries_gdf.to_file('timeseries.geojson', driver='GeoJSON')

# read the GeoJSON
timeseries_json = gpd.read_file('timeseries.geojson')
