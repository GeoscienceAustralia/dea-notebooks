import os
from osgeo import gdal, ogr
from rsgislib.segmentation import segutils
def imageSeg(InputNDVIStats,KEAFile,SegmentedKEAFile, SegmentedTiffFile, SegmentedPolygons, minPxls = 200):
    #convert tiff to .kea using gdal
    print('converting tif to a kea file...')
    gdal.Translate(KEAFile, InputNDVIStats, format='KEA', outputSRS='EPSG:3577')
    #run the image segmentation code
    segutils.runShepherdSegmentation(KEAFile, SegmentedKEAFile, numClusters=20, minPxls = minPxls)
    #convert imageSeg.kea file back into tiff
    print('converting back to tiff...')
    os.system("gdal_translate -of GTIFF -a_srs EPSG:3577 " + SegmentedKEAFile + " " + SegmentedTiffFile)
    #turn tiff into a polygon set  
    print('converting tiff to polygons...')
    os.system('gdal_polygonize.py ' + SegmentedTiffFile + ' -f' + ' ' + '"ESRI Shapefile"' + ' ' + SegmentedPolygons)
