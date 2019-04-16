
#stitching together the tiles from datacube stats to produce a mosaic tiff and then clipping to NDBA+NSW shapefile
qsub -I -l walltime=4:00:00,ncpus=8,mem=64Gb -P r78 -q express

#Then once use get your interactive node:

module use /g/data/v10/public/modules/modulefiles/
module load dea

gdalbuildvrt summary.vrt *.tif
gdal_translate summary.vrt summary.tif
