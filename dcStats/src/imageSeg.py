import os
from rsgislib.segmentation import segutils
def imageSeg(InputNDVIStats,KEAFile,SegmentedKEAFile, SegmentedTiffFile, SegmentedPolygons, minPxls = 200):
    #convert tiff to .kea using gdal
    os.system("gdal_translate -of KEA -a_srs EPSG:3577 " + InputNDVIStats + " " + KEAFile)
    #run the image segmentation code
    segutils.runShepherdSegmentation(KEAFile, SegmentedKEAFile, numClusters=20, minPxls = minPxls)
    #convert imageSeg.kea file back into tiff
    os.system("gdal_translate -of GTIFF -a_srs EPSG:3577 " + SegmentedKEAFile + " " + SegmentedTiffFile)
    #turn tiff into a polygon set
    os.system('gdal_polygonize.py ' + SegmentedTiffFile + ' -f' + ' ' + '"ESRI Shapefile"' + ' ' + SegmentedPolygons)
