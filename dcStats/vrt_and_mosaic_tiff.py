
# start an interactive node and then module load libraries
# module use /g/data/v10/public/modules/modulefiles/
# module load dea

cpus=4
directory = "/g/data/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/summer87_90/ndviArgMaxMin/"

import fnmatch
import os
from multiprocessing import Pool

#multithreaded version of mosaic
def mosaicTiffs(folder):
    os.chdir(directory + folder)
    os.system("gdal_translate "\
       "-co BIGTIFF=YES "\
       "-co COMPRESS=DEFLATE "\
       "-co ZLEVEL=9 "\
       "-co PREDICTOR=1 "\
       "-co TILED=YES "\
       "-co BLOCKXSIZE=1024 "\
       "-co BLOCKYSIZE=1024 "\
       "ndviArgMaxMin_" + folder + "1101_mosaic.vrt " + "ndviArgMaxMin_" + folder + "1101_mosaic.tif")

folder = os.listdir(directory)

if __name__ == '__main__':
    pool = Pool(cpus)  
    pool.map(mosaicTiffs, folder)
