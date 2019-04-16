import os

#build compressed mosaic
directory = "/g/data1a/r78/cb3058/dea-notebooks/dcStats/results/mdb_NSW/summer/previous_run/ndviArgMaxMin/"
for folder in os.listdir(directory):
    os.chdir(directory + folder)
    os.system("gdal_translate "\
       "-co BigTIFF=YES"\
       "-co COMPRESS=DEFLATE "\
       "-co ZLEVEL=9 "\
       "-co PREDICTOR=1 "\
       "-co TILED=YES "\
       "-co BLOCKXSIZE=1024 "\
       "-co BLOCKYSIZE=1024 "\
       + folder + "_mosaic.vrt " + folder + "_mosaic.tif")