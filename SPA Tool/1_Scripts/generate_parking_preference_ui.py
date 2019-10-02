# Author: RSG (Justin Culp, GISP; David Grover, PE)
# Date: 08-30-2019
#
# Description: 
# Requires: ArcGIS 10.2 Desktop Basic
#

# Import arcpy module
import arcpy, os
from arcpy import env
import pandas as pd
from math import radians, cos, sin, asin, sqrt
from datetime import datetime
import csv

# Get relative path for working directory
pathName = os.path.dirname(sys.argv[0])
rootStr = str(pathName.split("\\")[:-1])
rootDir = rootStr.lstrip().replace(", ", "\\").replace("'", "").replace("[", "").replace("]", "")
print("Root Directory: "+rootDir)

# Define global variables
## Input varibales:
gen_shp = arcpy.GetParameterAsText(0)   # Williston_Employment.shp"
lot_shp = arcpy.GetParameterAsText(1)   # Williston_Parking.shp"

in_ref = 4326   # WGS 1984
max_walk_dist = arcpy.GetParameterAsText(2)     # ".25 MILES"

## Intermediate variables:
temp_csv = os.path.join(rootDir, r"2_Data\Output Data\temp_results.csv")

## Output variables:
outFolder = arcpy.GetParameterAsText(3)
outFile = arcpy.GetParameterAsText(4)
pref_csv = os.path.join(outFolder, outFile+".csv")
list_csv = os.path.join(outFolder, outFile+"_list.csv")

# Subroutines:
def CalculateGCD(lon1, lat1, lon2, lat2):
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    mi = km * 0.621371
    return mi


# Define functions (Geoprocessing steps):
def CreateIntermediateWorkspace():
    # Define geodatabase workspace
    gdb_folder = os.path.join(rootDir, "2_Data")
    gdb_name = "Working_Data.gdb"
    gdb_path = os.path.join(gdb_folder, gdb_name)
    # Check if geodatabase exists and create new
    if not arcpy.Exists(gdb_path):
        new_gdb = arcpy.CreateFileGDB_management(gdb_folder, gdb_name)
    else:
        arcpy.Delete_management(os.path.join(gdb_folder, gdb_name))
        new_gdb = arcpy.CreateFileGDB_management(gdb_folder, gdb_name)
    return gdb_path


def JoinParkingLots2Generator(working_gdb):
    # Determine spatial reference of Generator data and convert to wgs 1984 if needed, create working copy.
    if arcpy.Describe(gen_shp).spatialReference != in_ref:
        empPnts = arcpy.Project_management(gen_shp, os.path.join(working_gdb, "Generator"), in_ref)
    else:
        empPnts = arcpy.Select_analysis(gen_shp, os.path.join(working_gdb, "Generator"))
    # Add geographic fields
    arcpy.AddField_management(empPnts, "Gen_UID", "LONG")
    arcpy.AddField_management(empPnts, "Gen_Lon", "DOUBLE")
    arcpy.AddField_management(empPnts, "Gen_Lat", "DOUBLE")
    # Add new unique id
    with arcpy.da.UpdateCursor(empPnts, "Gen_UID") as rows:
        for i, row in enumerate(rows, 1):
            row[0] = i
            rows.updateRow(row)
    arcpy.CalculateField_management(empPnts, "Gen_Lon", "!shape.firstpoint.X!", "PYTHON_9.3", "")
    arcpy.CalculateField_management(empPnts, "Gen_Lat", "!shape.firstpoint.Y!", "PYTHON_9.3", "")
    # Determine spatial reference of parking data and convert to wgs 1984 if needed, create working copy.
    if arcpy.Describe(lot_shp).spatialReference != in_ref:
        lotPoly = arcpy.Project_management(lot_shp, os.path.join(working_gdb, "Parking"), in_ref)
    else:
        lotPoly = arcpy.Select_analysis(lot_shp, os.path.join(working_gdb, "Parking"))
    # Create parking polygon centroids
##    lotPnts = arcpy.FeatureToPoint_management(lotPoly, os.oath.join(working_gdb, "Parking_Centroids"), "INSIDE")
    # Add geographic fields
    arcpy.AddField_management(lotPoly, "Lot_UID", "LONG")
    arcpy.AddField_management(lotPoly, "Lot_Lon", "DOUBLE")
    arcpy.AddField_management(lotPoly, "Lot_Lat", "DOUBLE")
    # Add new unique id
    with arcpy.da.UpdateCursor(lotPoly, "Lot_UID") as rows:
        for i, row in enumerate(rows, 1):
            row[0] = i
            rows.updateRow(row)
    arcpy.CalculateField_management(lotPoly, "Lot_Lon", "!shape.centroid.X!", "PYTHON_9.3", "")
    arcpy.CalculateField_management(lotPoly, "Lot_Lat", "!shape.centroid.Y!", "PYTHON_9.3", "")
    # Spatial join Generator points and parking locations
    empLotsSJ = arcpy.SpatialJoin_analysis(empPnts, lotPoly, os.path.join(working_gdb, "Gen_Parking_SJ"), "JOIN_ONE_TO_MANY", "", "", "INTERSECT", max_walk_dist, "")
    # Write spatial join results to temp csv
    arcpy.TableToTable_conversion(empLotsSJ, os.path.join(rootDir, r"2_Data\Output Data"), "temp_results.csv")

def RankParkingPreferenceByWalkDistance():
    # Read results into dataframe
    emplotsDf = pd.read_csv(temp_csv, sep=',', header=0)
    emplotsDf = emplotsDf.filter(['Gen_UID', 'Gen_Lon', 'Gen_Lat', 'Lot_UID', 'Lot_Lon', 'Lot_Lat'])
    # Return great circle walk distance for each lot in miles
    emplotsDf['Lot_Dist'] = emplotsDf.apply(lambda row: CalculateGCD(row['Gen_Lon'], row['Gen_Lat'], row['Lot_Lon'], row['Lot_Lat']), axis=1)
    emplotsDf = emplotsDf.sort_values(['Gen_UID', 'Lot_Dist'], ascending=True)
    # Get list of unique Generator ID's, rank lots from 1-n based on distance for each Generator location
    empIds = list(emplotsDf.Gen_UID.unique())
    lotPrefDf = pd.DataFrame()
    lotPrefDict = dict()
    for id in empIds:
        rankEmpLot = emplotsDf.loc[emplotsDf['Gen_UID'] == id]
        rankEmpLot['Lot_Pref'] = rankEmpLot['Lot_Dist'].rank(method='min', ascending=True) #method='min'
        lotPrefDf = pd.concat([lotPrefDf,rankEmpLot])
        lotPrefDict[id] = list(rankEmpLot['Lot_UID'])
    lotPrefDf.to_csv(pref_csv, sep=',', index=False)
    with open(list_csv, 'w') as f:
        for key in lotPrefDict.keys():
            f.write("%f,%s\n"%(key,';'.join([str(int(k)) for k in lotPrefDict[key]])))    

if __name__== "__main__":
    print("Script Start Time: ", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    wrk_gdb = CreateIntermediateWorkspace()
    JoinParkingLots2Generator(wrk_gdb)
    RankParkingPreferenceByWalkDistance()
    arcpy.Delete_management(temp_csv)
##    arcpy.Delete_management(wrk_gdb)
    print("Script End Time: ", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))









