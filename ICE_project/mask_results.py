import numpy as np
import xarray as xr
import geopandas as gpd
import os
from multiprocessing import Pool
#import custom functions
import sys
sys.path.append('src')
import SpatialTools
from transform_tuple import transform_tuple

cpus=1
mask_dir = "/g/data/r78/cb3058/dea-notebooks/ICE_project/data/spatial/NSWmask_and_LSmask.shp"
#nmdb_mask_allDryYears_merged.shp
#NSWmask_and_LSmask.shp
#nmdb_OEH2017_irrigated.shp
directory = "/g/data/r78/cb3058/dea-notebooks/ICE_project/results/nmdb/"
input_suffix = "_multithreshold_60Thres"
output_suffix = "_OEHandLS_masked"
#_OEHandLS_masked
#_LS80_masked
#_OEHonly_masked

x = range(2013,2014,1)
years = []
for i in x:
    nextyear = str(i + 1)[2:]
    y = str(i) + "_" + nextyear
    years.append(str(y))
years =  [e for e in years if e not in ('2011_12', '2012_13')]
years.sort()
     
folders = os.listdir(directory)
folders.sort()
folders = folders[24]

inputs=[]
for year, folder in zip(years, folders):
    inputs.append(directory+"nmdb_Summer"+year+"/nmdb_Summer" + year + input_suffix + ".tif")

def clip_tiff(tif):
    print("working on year: " + tif[88:-27])
    a = xr.open_rasterio(tif).squeeze()
    
    transform, projection = transform_tuple(a, (a.x, a.y), epsg=3577)
    width,height = a.shape
    
    mask = SpatialTools.rasterize_vector(mask_dir,
           height, width, transform, projection, raster_path=None)
    b = a.where(mask)

    SpatialTools.array_to_geotiff(tif[:-4]+output_suffix+".tif",
              b.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=np.nan)
    
#     os.system('gdal_polygonize.py ' + tif[:-4]+"_60Thres_masked.tif" + ' -f' + ' ' + '"ESRI Shapefile"' + ' ' + tif[:-4]+"_60Thres_masked.shp")

#     gdf = gpd.read_file(tif[:-4]+"_60Thres_masked.shp")
#     gdf['area'] = gdf['geometry'].area
#     gdf.to_file(tif[:-19]+"_60Thres_IrrigatedMasked.shp")
#     print("finished processing: "+tif[88:-19])
    
pool = Pool(cpus)    
pool.map(clip_tiff, inputs) 
    

