
#INSTRUCTIONS
# 1. start an interactive node with lots of memory
#qsub -I -q expressbw -l walltime=3:00:00,mem=256GB,ncpus=7

# 2. module load the librariesand then module load libraries
# module use /g/data/v10/public/modules/modulefiles/
# module load dea

#3. Run the following script:

#user inputs
cpus=4
directory = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/ndvi_max/"
filenames= "ndvi_max"

import fnmatch
import os
from multiprocessing import Pool

#multithreaded version of mosaic
def mosaicTiffs(folder):
    os.chdir(directory + folder)
	os.system("gdalbuildvrt " + filenames + "_" + folder + "1101_mosaic.vrt *.tif")
    os.system("gdal_translate "\
       "-co BIGTIFF=YES "\
       "-co COMPRESS=DEFLATE "\
       "-co ZLEVEL=9 "\
       "-co PREDICTOR=1 "\
       "-co TILED=YES "\
       "-co BLOCKXSIZE=1024 "\
       "-co BLOCKYSIZE=1024 "\
       filenames + folder + "1101_mosaic.vrt " + filenames + "_" + folder + "1101_mosaic.tif")

folder = os.listdir(directory)

pool = Pool(cpus)  
pool.map(mosaicTiffs, folder)














