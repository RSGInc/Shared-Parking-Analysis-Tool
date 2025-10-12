# Analyzing the Data

## GeoJSONs & Kepler.GL

After a complete SUPM run several opportunities exist for post processing to analyze the results. 

The SUPM produces a `timeseries.csv` file that includes a long file with all lots and specific hour of the year and various data, such as percent occupied. 



A python file can convert the data in the `timeseries.csv` into a GeoJSON with the shapefile for the parking lots (parking supply). 

Run the `timeseries_to_geojson.py` script. In the script point to key files:

- Timeseries CSV 
- Parking Lots shapefile. 

The python script creates the GeoJSON file. The GeoJSON can then be visualized in various GIS services and tools. 

The one recommended is the Kepler.GL service. The Kepler.GL is an open source visualizer for large datasets. 

- Website for Kepler.GL  https://kepler.gl/ 

The method that has been used successfully uses a Kepler.GL Extension in Visual Studio that reads in the GeoJSON to create an interactive map that can be saved as an HTML. The HTML is a convenient way to share the results from the SUPM in a form that can be visualized to show parking demand across times of the day, weekdays and weekends, and months of the year. 

The Extension is Geo Data Viewer in VisualStudio

![image-20251011202904727](../assets/media/image-20251011202904727.png)


Using the extension in VisualStudio you can import the GeoJSON, navigate the maps, set the conditions (filters and queries), and export as an HTML file.

- Layers:

  - select the polygon
  - select fill color and then select the field to analyze. The 'frac_full' is the percentage of spaces occupied. 

  + ###### Filters: 

    + Select the hour (the time of the data)
    + Day (select weekday or weekend)
    + Month (select the month of the year)

    

![image-20251011203814780](../assets/media/image-20251011203814780.png)



In the top right corner of the map, there is a Save button that can export to HTML.

![image-20251011204331288](../assets/media/Kepler_save.png)



The HTML file includes the filter that was selected and then allows the user to interact with the data. 



