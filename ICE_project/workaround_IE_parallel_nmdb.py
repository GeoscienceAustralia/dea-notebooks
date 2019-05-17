
import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from osgeo import gdal, ogr
import os
#from multiprocessing import Pool, cpu_count
from rsgislib.segmentation import segutils

#import custom functions
import sys
sys.path.append('src')
import DEAPlotting, SpatialTools
from transform_tuple import transform_tuple

############
#User Inputs
############

#how many cpus should the job be distrubuted over?
# cpus = 8

# where are the dcStats MaxNDVI tifs?
MaxNDVItiffs = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/nmdb/"

# where should I put the results?
results ='/g/data/r78/cb3058/dea-notebooks/ICE_project/results/nmdb/'

#what season are we processing (Must be 'Summmer' or 'Winter')?
season = 'Summer'

#Input your area of interest's name
AOI = 'nmdb'

# script proper-----------------------------

def irrigated_extent(tif):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("starting processing of " + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    results_ = results
    
    if season == 'Summer':
        year = tif[11:15]
        nextyear = str(int(year) + 1)[2:] 
        year = year + "_" + nextyear
        year = season + year
    if season == 'Winter':
        year = tif[7:11]
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
    print("converting tiff to kea")
    gdal.Translate(KEAFile, InputNDVIStats, format='KEA', outputSRS='EPSG:3577')
    
    # Run segmentation, with creation of clump means
    print('running image seg')
    segutils.runShepherdSegmentation(KEAFile, SegmentedKEAFile, meanImage,
                        tmpath='/g/data1a/r78/cb3058/dea-notebooks/ICE_project/tmps/'+tif,
                        numClusters=20, minPxls=100)
    #open the segment means file
    segment_means = xr.open_rasterio(meanImage).squeeze()
    
    #reclassify and threshold by different values
    a = np.where(segment_means.values>=0.8, 80, segment_means.values)
    b = np.where((a>=0.75) & (a<0.8), 75, a)
    c = np.where((b>=0.70) & (b<0.75), 70, b)
    d = np.where(c>=70, c, np.nan)
    
    
    print('exporting the multithreshold as Gtiff')
    transform, projection = transform_tuple(segment_means, (segment_means.x, segment_means.y), epsg=3577)
    #find the width and height of the xarray dataset we want to mask
    width,height = segment_means.shape
    
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_multithreshold.tif",
                  d, geo_transform = transform, 
                  projection = projection, 
                  nodata_val=np.nan)
    
    #converting irrigated areas results to polygons
    print('converting multithreshold tiff to polygons...')
    multithresholdTIFF = results_ + AOI + "_" + year + "_multithreshold.tif"
    multithresholdPolygons = results_ + AOI + '_' + year + '_multithreshold.shp'
    
    os.system('gdal_polygonize.py ' + multithresholdTIFF + ' -f' + ' ' + '"ESRI Shapefile"' + ' ' + multithresholdPolygons)
    
    #filter by the area of the polygons to get rid of any forests etc
    print('filtering polygons by size, exporting, then rasterizing')
    gdf = gpd.read_file(multithresholdPolygons)
    gdf['area'] = gdf['geometry'].area
    smallArea = gdf['area'] <= 50000000
    gdf = gdf[smallArea]
    #export shapefile
    print('exporting irrigated shapefile')
    gdf.to_file(results_ + AOI + "_" + year + "_Irrigated.shp")
    
    z = gdf[gdf.DN==80]
    z = z[z.area>100000]
    z.to_file(results_ + AOI + "_" + year + "_80polys_>10ha.shp")
        
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print('finished processing ' + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    
if __name__ == '__main__':
    irrigated_extent(sys.argv[1])
    
# maxNDVItiffFiles = os.listdir(MaxNDVItiffs)    
#     pool = Pool(cpus)  
#     pool.map(irrigated_extent, maxNDVItiffFiles)

















