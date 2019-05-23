import numpy as np
import xarray as xr
import os
from multiprocessing import Pool, cpu_count
import geopandas as gpd

#import custom functions
import sys
sys.path.append('src')
import SpatialTools
from transform_tuple import transform_tuple

cpus=4

x = range(1987,2019,1)
years = []
for i in x:
    nextyear = str(i + 1)[2:]
    y = str(i) + "_" + nextyear
    years.append(str(y))
years =  [e for e in years if e not in ('2011_12', '2012_13')]
years.sort()
    
directory = "/g/data/r78/cb3058/dea-notebooks/ICE_project/results/nmdb/"    
folders = os.listdir(directory)
folders.sort()

inputs=[]
for year, folder in zip(years, folders):
    inputs.append(directory+folder+"/"+"nmdb_Summer"+ year+"_ClumpMean.kea")

# print(inputs)    
    
def lowerThres(tif):
       
    results_ = tif[:-32]
    AOI='nmdb'
    year='Summer' + tif[69:-33]
    
    #open the segment means file 
    segment_means = xr.open_rasterio(tif).squeeze()
    
    #reclassify and threshold by different values
    a = np.where(segment_means.values>=0.8, 80, segment_means.values)
    b = np.where((a>=0.75) & (a<0.8), 75, a)
    c = np.where((b>=0.70) & (b<0.75), 70, b)
    d = np.where((c>=0.65) & (c<0.70), 65, c)
    e = np.where(d>=65, d, np.nan)
    
    
    print('exporting the multithreshold as Gtiff')
    transform, projection = transform_tuple(segment_means, (segment_means.x, segment_means.y), epsg=3577)
    #find the width and height of the xarray dataset we want to mask
    width,height = segment_means.shape
    
    SpatialTools.array_to_geotiff(results_ + AOI + "_" + year + "_multithreshold_65Thres.tif",
                  e, geo_transform = transform, 
                  projection = projection, 
                  nodata_val=np.nan)
    
#     #converting irrigated areas results to polygons
#     print('converting multithreshold tiff to polygons...')
#     multithresholdTIFF = results_ + AOI + "_" + year + "_multithreshold_lwrThres.tif"
#     multithresholdPolygons = results_ + AOI + '_' + year + '_multithreshold_lwrThres.shp'
    
#     os.system('gdal_polygonize.py ' + multithresholdTIFF + ' -f' + ' ' + '"ESRI Shapefile"' + ' ' + multithresholdPolygons)
    
#     #filter by the area of the polygons to get rid of any forests etc
#     print('filtering polygons by size, exporting, then rasterizing')
#     gdf = gpd.read_file(multithresholdPolygons)
#     gdf['area'] = gdf['geometry'].area
#     smallArea = gdf['area'] <= 50000000
#     gdf = gdf[smallArea]
#     #export shapefile
#     print('exporting irrigated shapefile')
#     gdf.to_file(results_ + AOI + "_" + year + "_Irrigated_lwrThres.shp")
    
#     z = gdf[gdf.DN==80]
#     z = z[z.area>100000]
#     z.to_file(results_ + AOI + "_" + year + "_80polys_10ha_lwrThres.shp")
        
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print('finished processing ' + tif)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

pool = Pool(cpus)  
pool.map(lowerThres, inputs)
















