"""

This script ingest a geotiff of maximum NDVI over a summer period,
then runs image segmentation, thresholds zonal stats over 
the segments, and filters by area to produce a first pass estimate of
Summer irrigated area.

Code is multiprocessed so will conduct the analysis across n number of
specified cpus. Adjust the user inputs, and then run the script
through the terminal:
 
 python3 Summer_irrigated_area.py
 
 
NOTE: Look out for the string slicing on line 66, this can throw
    errors if the filenames are different from those I've specified.
 
"""


#import libraries
import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from osgeo import gdal, ogr
import os
from multiprocessing import Pool, cpu_count
from rsgislib.segmentation import segutils
from datacube.helpers import write_geotiff
from src import SpatialTools

############
#User Inputs
############

# where are the dcStats MaxNDVI tifs?
MaxNDVItiffs = "data/ndvi_max/"

# where should I put the results?
results ='results/'

#what season are we processing?
season = 'Summer'

#Input your area of interest's name
AOI = 'Tasmania'

output_suffix = '_multithreshold_65Thres'

mask_dir = 'data/IrrigableLand.shp'

cpus = 4


#----Script proper-------------------------

def irrigated_extent(tif):

    print("starting processing of " + tif)
    
    #reset the results path
    results_ = results
    
    #set up inputs
    year = tif[9:13]
    nextyear = str(int(year) + 1)[2:] 
    year = year + "_" + nextyear
    year = season + year

    #Creating a folder to keep things neat
    directory = results_ + AOI + "_" + year
    if not os.path.exists(directory):
        os.mkdir(directory)
    
    results_ = results_ + AOI + "_" + year + "/"
    
    #inputs to GDAL and RSGISlib
    InputNDVIStats = MaxNDVItiffs + tif
    SegmentedKEAFile = results_ + AOI + '_' + year + '_sheperdSEG.kea'
    meanImage = results_ + AOI + '_' + year + "_ClumpMean.kea"
    KEAFile = results_ + AOI + '_' + year + '.kea'
    
    # Change the tiff to a kea file
    gdal.Translate(KEAFile, InputNDVIStats, format='KEA', outputSRS='EPSG:3577')
    
    # Run segmentation, with creation of clump means
    segutils.runShepherdSegmentation(KEAFile, SegmentedKEAFile, meanImage,
                        tmpath='data/tmp/'+tif,
                        numClusters=20, minPxls=100)
    
    #open the segment means file
    segment_means = xr.open_rasterio(meanImage).squeeze()
    
    #reclassify
    a = np.where(segment_means.values>=0.8, 80, segment_means.values)
    b = np.where((a>=0.75) & (a<0.8), 75, a)
    c = np.where((b>=0.70) & (b<0.75), 70, b)
    d = np.where((c>=0.65) & (c<0.70), 65, c)
    e = np.where(d>=65, d, np.nan)
    
    #export geotiff
    transform, projection = SpatialTools.geotransform(segment_means, (segment_means.x, segment_means.y), epsg=3577)
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + output_suffix +".tif",
                  e, geo_transform = transform, 
                  projection = projection, 
                  nodata_val=np.nan)
    
    #polygonise the array
    multithresholdTIFF = results_ + AOI + "_" + year + output_suffix +".tif"
    multithresholdPolygons = results_ + AOI + '_' + year + output_suffix +".shp"
    os.system('gdal_polygonize.py ' + multithresholdTIFF + ' -f' + ' ' + '"ESRI Shapefile"' + ' ' + multithresholdPolygons)
    
    #filter by the area of the polygons to get rid of any forests etc
    gdf = gpd.read_file(multithresholdPolygons)
    gdf['area'] = gdf['geometry'].area
    smallArea = gdf['area'] <= 5000000 #500 ha
    gdf = gdf[smallArea]
    
    gdf = gdf[gdf.DN==80]
    gdf = gdf[gdf.area>100000] #10 ha
    
    gdf.to_file(results_ + AOI + "_" + year + "_80polys_10ha.shp")

    print('finished processing ' + tif)
    
maxNDVItiffFiles = os.listdir(MaxNDVItiffs)    
maxNDVItiffFiles.sort()
pool = Pool(cpus)  
pool.map(irrigated_extent, maxNDVItiffFiles)