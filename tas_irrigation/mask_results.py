"""
This script will take the curated 'irrigable area' shapefile mask and use it mask the 
multithreshold.tif output from the script 'Summer_irrigated_area.py'
The results will be a shapefile called ,<AOI><year>_irrigated_<suffix>.shp.
These are the final estimates of summer irrigated area.

Code is multiprocessed so will conduct the analysis across n number of
specified cpus. Adjust the user inputs, and then run the script
through the terminal:
 
 python3 mask_results.py
 
NOTE: Look out for the string slicing on line 88, this can throw
    errors if the filenames are different from those I've specified.
 
"""


#import libraries
import numpy as np
import xarray as xr
import geopandas as gpd
import os
from multiprocessing import Pool
#import custom functions
import sys
sys.path.append('src')
import SpatialTools

##############
# User Inputs
#############

#number of cpus
cpus=4
#path to the masking shpefile
mask_dir = "data/irrigable_mask_NE.shp"
#directory to where the results are stored
directory = "results/"
#suffix of the mulithreshold tiff
input_suffix = "_multithreshold_65Thres"
#suffix to place at the end of your final results
output_suffix = "_LS_masked"


#generate input strings for the code 
x = range(2000,2019,1)
years = []
for i in x:
    nextyear = str(i + 1)[2:]
    y = str(i) + "_" + nextyear
    years.append(str(y))
#remove years that dont have satellite coverage
years =  [e for e in years if e not in ('2011_12', '2012_13')]
years.sort()

inputs=[]
for year in years:
    inputs.append(directory+"Tasmania_Summer"+year+"/Tasmania_Summer" + year + input_suffix + ".tif")

    
def clip_tiff(tif):
    print("working on: " + tif)
    
    #open tiff, rasterize mask
    a = xr.open_rasterio(tif).squeeze()
    transform, projection = SpatialTools.geotransform(a, (a.x, a.y), epsg=3577)
    width,height = a.shape
    mask = SpatialTools.rasterize_vector(mask_dir,
           height, width, transform, projection, raster_path=None)
    
    #mask the geotiff
    b = a.where(mask)
    
    #export masked geotiff
    SpatialTools.array_to_geotiff(tif[:-4]+output_suffix+".tif",
              b.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=np.nan)
    
    #polygonize
    os.system('gdal_polygonize.py ' + tif[:-4]+output_suffix+".tif" + ' -f' + ' ' + '"ESRI Shapefile"' + ' ' + tif[:-4]+output_suffix+ ".shp")
    
    #filter by area and export shapefile
    gdf = gpd.read_file(tif[:-4]+output_suffix+ ".shp")
    gdf['area'] = gdf['geometry'].area
    gdf = gdf[gdf.area>100000]
    gdf.to_file(tif[:-27]+ "_Irrigated" +output_suffix+ ".shp")
    
    print("finished processing: "+tif)

#run code across n cpus
pool = Pool(cpus)    
pool.map(clip_tiff, inputs) 
    

