#-----INSTRUCTIONS----------------------------------------
# Enter relevant information in the user inputs section 
# then follow the steps below

# start up an interactive session on Raijin eg:
#     qsub -I -q expressbw -l walltime=2:00:00,mem=256GB,ncpus=7

# Then navigate to your directory with the code and do a DEA module load        
#     cd /g/data/r78/cb3058/dea-notebooks/segmentation/
#     module use /g/data/v10/public/modules/modulefiles/
#     module load dea

# Ensure you have 'pathos' installed and then point to it. To install 
# a python library in a location that Raijin can see:
# 	 pip install --target=/g/data/r78/cb3058/dea-notebooks/segmentation/python_packages <packageName>
#    export PYTHONPATH=/g/data/r78/cb3058/dea-notebooks/segmentation/src/python_packages/

#---------------------------------------------------------

#!!!!!!!!!!!!!!!!!
#  User inputs
#!!!!!!!!!!!!!!!!!

#Location string of the geotiff you wish to segment
inputTiff = "data/nmdb_Summer2017_18_NDVI_max.tif"

#Location string of the .KEA file the geotiff will be converted too
InputKEA = "data/nmdb_Summer2017_18_NDVI_max.kea"

#Location string of clumps mean .KEA file that will be output 
ClumpsFile = "results/nmdb_Summer2017_18_NDVI_max_OutClumps.kea"

#Location string of the segments zonal means of input Tiff 
meanImageTiff = "results/nmdb_Summer2017_18_NDVI_max_ClumpMean.tif"

#Location to a folder to store temporary files during segmentation
temp = 'tmps/'

#How many cpus will this run on?
ncpus=12

# what fraction of a tile should contain valid data? Below this threshold
# a tile will be merged with its neighbour. 
validDataTileFraction = 0.3

#enter the tile size parameters (in number of pixels)
width = 8000
height = 8000

#-------------Script-------------------------------------------------------------
from osgeo import gdal
import os
from rsgislib.segmentation import meanImage
import rsgislib
from pathos.multiprocessing import ProcessingPool as Pool
import dill
import xarray as xr
import numpy as np
#import custom functions
import sys
sys.path.append('src')
import tiledSegThreaded
from transform_tuple import transform_tuple
from SpatialTools import array_to_geotiff

#run segementation algorithm and time the code
import time
start = time.time()
tiledSegThreaded.performTiledSegmentation(InputKEA, ClumpsFile, tmpDIR=temp, numClusters=20, validDataThreshold=validDataTileFraction,
                                    tileWidth=width, tileHeight=height, minPxls=100, ncpus=ncpus)
end = time.time()
print(end - start)

# Attribute segments with zonal mean of input image
meanImage(inputTiff, ClumpsFile, meanImageTiff, "GTIFF",rsgislib.TYPE_32FLOAT)

#convert segments result into geotiff (gdal.Translate is failing for some reason?)
a = xr.open_rasterio(ClumpsFile).squeeze()
transform, projection = transform_tuple(a, (a.x, a.y), epsg=3577)
width,height = a.shape
array_to_geotiff(ClumpsFile[:-4]+".tif",
      a.values, geo_transform = transform, 
      projection = projection, 
      nodata_val=-999)