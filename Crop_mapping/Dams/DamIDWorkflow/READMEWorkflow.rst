These notebooks allow you to generate a polygon set of water bodies using WOFS frequency stats. 
These polygons are then used for a polygon drill into the wofs_albers tiles, and the percentage of pixels 
within the water body classifed as wet at each time step is recorded and written to csv. 

To run this workflow, you will need to use the following notebooks:
(Note that the WOFS frequency netCDF files need to be produced using the datacube-stats code prior to 
using these notebooks). 
1. FindLotsofDamsUsingWOFLs.ipynb
    * Requires a folder of netCDF tiles of WOFS summaries for the chosen time and spatial area
2. GetDamTimeHistoryParallel.ipynb
    * This code requires that you assign a record attribute called 'ID' to the shapefile
    * Uses the shape file written out by notebook one, and generates csv files of the polygon water history
    * Note that this code is parallelised to run on the VDI
3. QuickPlotofWaterBodyTimeseries.ipynb
    * This quick and dirty notebook takes in a water body ID (you can find this by pulling the shapefile from 
    notebook one into QGIS) and quickly plots up the water timeseries. 
