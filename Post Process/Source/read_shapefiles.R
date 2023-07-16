### read parking shapefile - takes a long time, so saved as rds. redo if shapefile changes
parking_shp = readOGR(dsn = paste(model_dir,"data",sep="/"),layer=supply_shp,stringsAsFactors = FALSE)
parking = parking_shp@data %>%
  mutate(LOT_UID = as.numeric(LOT_UID)
         ,SPACE_TOT = as.numeric(SPACE_TOT)
         ,LOT_GEN_ID = as.numeric(LOT_GEN_ID)
         ,RESTRICT = as.numeric(RESTRICT))

rm(parking_shp)

### read generator shapefile
generator_shp = readOGR(dsn = paste(model_dir,"data",sep="/"),layer=demand_shp,stringsAsFactors = FALSE)
generators = generator_shp@data %>%
  mutate(GEN_UID = as.numeric(GEN_UID))

rm(generator_shp)
