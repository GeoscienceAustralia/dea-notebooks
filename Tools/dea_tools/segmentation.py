# segmentation.py
"""

A DEA customized version of the tiledsegsingle.py module
implemented by the python package RSGISlib.  It has been adapted to run a tiled,
parallel image segmentation across a specified number of cpus.

NOTE: the only function that 99% of users will need to call is "performTiledSegmentation"

Documentation for the RSGISlib Image Segmentation Module can be found here:
https://www.rsgislib.org/rsgislib_segmentation.html


License
-------
The code in this notebook is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth
Africa data is licensed under the Creative Commons by Attribution 4.0
license (https://creativecommons.org/licenses/by/4.0/).

Contact
-------
If you need assistance, please post a question on the Open Data
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube)
using the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, file one on
Github: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new


.. autosummary::
   :nosignatures:
   :toctree: gen

"""

import glob
import os.path
import os
import rsgislib
from rsgislib.imageutils import tilingutils
from rsgislib.segmentation import segutils
from rsgislib import rastergis
from rsgislib import imageutils
from rsgislib import segmentation
import dill
from pathos.multiprocessing import ProcessingPool as Pool
from osgeo import gdal
from rios import rat
import json
import shutil


class RSGISTiledShepherdSegmentationSingleThread(object):
    """
    A class for running the tiled version of the shepherd segmentation algorithm.
    This can process larger images than the single scene version with a smaller
    memory footprint.

    This version has been adapted to run over multiple cpus. 

    It is not intended that this class will be directly used. Please use the 
    function 'performTiledSegmentation' to call this functionality. 
    """

    def findSegStatsFiles(self, tileImg, segStatsInfo):
        gdalDS = gdal.Open(tileImg, gdal.GA_ReadOnly)
        geotransform = gdalDS.GetGeoTransform()
        if not geotransform is None:
            xMin = geotransform[0]
            yMax = geotransform[3]

            xRes = geotransform[1]
            yRes = geotransform[5]

            width = gdalDS.RasterXSize * xRes
            if yRes < 0:
                yRes = yRes * (-1)
            height = gdalDS.RasterYSize * yRes
            xMax = xMin + width
            yMin = xMax - height

            xCen = xMin + (width / 2)
            yCen = yMin + (height / 2)
        gdalDS = None

        first = True
        minDist = 0.0
        minKCenFile = ""
        minStchStatsFile = ""
        for tileName in segStatsInfo:
            tileXCen = segStatsInfo[tileName]['CENTRE_PT']['X']
            tileYCen = segStatsInfo[tileName]['CENTRE_PT']['Y']
            dist = ((tileXCen - xCen) * (tileXCen - xCen)) + \
                ((tileYCen - yCen) * (tileYCen - yCen))
            if first:
                minKCenFile = segStatsInfo[tileName]['KCENTRES']
                minStchStatsFile = segStatsInfo[tileName]['STRETCHSTATS']
                minDist = dist
                first = False
            elif dist < minDist:
                minKCenFile = segStatsInfo[tileName]['KCENTRES']
                minStchStatsFile = segStatsInfo[tileName]['STRETCHSTATS']
                minDist = dist

        return minKCenFile, minStchStatsFile

    def performStage1Tiling(self, inputImage, tileShp, tilesRat, tilesBase,
                            tilesMetaDIR, tilesImgDIR, tmpDIR, width, height,
                            validDataThreshold):
        tilingutils.createMinDataTiles(inputImage, tileShp, tilesRat, width,
                                       height, validDataThreshold, None, False,
                                       True, tmpDIR)
        tilingutils.createTileMaskImagesFromClumps(tilesRat, tilesBase,
                                                   tilesMetaDIR, "KEA")
        rsgisUtils = rsgislib.RSGISPyUtils()
        dataType = rsgisUtils.getRSGISLibDataTypeFromImg(inputImage)
        tilingutils.createTilesFromMasks(inputImage, tilesBase, tilesMetaDIR,
                                         tilesImgDIR, dataType, 'KEA')

    def performStage1TilesSegmentation(self, tilesImgDIR, stage1TilesSegsDIR,
                                       tmpDIR, tilesBase, tileSegInfoJSON,
                                       strchStatsBase, kCentresBase,
                                       numClustersVal, minPxlsVal, distThresVal,
                                       bandsVal, samplingVal, kmMaxIterVal,
                                       ncpus):
        imgTiles = glob.glob(os.path.join(tilesImgDIR, tilesBase + "*.kea"))

    def performStage1TilesSegmentation(self, tilesImgDIR, stage1TilesSegsDIR,
                                       tmpDIR, tilesBase, tileSegInfoJSON,
                                       strchStatsBase, kCentresBase,
                                       numClustersVal, minPxlsVal, distThresVal,
                                       bandsVal, samplingVal, kmMaxIterVal,
                                       ncpus):
        imgTiles = glob.glob(os.path.join(tilesImgDIR, tilesBase + "*.kea"))

        def threadedTiledImgSeg(imgTile):
            baseName = os.path.splitext(os.path.basename(imgTile))[0]
            tileID = baseName.split('_')[-1]
            clumpsFile = os.path.join(stage1TilesSegsDIR,
                                      baseName + '_segs.kea')
            tmpStatsJSON = os.path.join(tilesImgDIR,
                                        baseName + '_segstats.json')
            strchStatsOutFile = strchStatsBase + "_" + tileID + '.txt'
            kCentresOutFile = kCentresBase + "_" + tileID
            print(clumpsFile)

            try:
                segutils.runShepherdSegmentation(
                    imgTile,
                    clumpsFile,
                    outputMeanImg=None,
                    tmpath=os.path.join(tmpDIR, tileID + '_segstemp'),
                    gdalformat='KEA',
                    noStats=False,
                    noStretch=False,
                    noDelete=False,
                    numClusters=numClustersVal,
                    minPxls=minPxlsVal,
                    distThres=distThresVal,
                    bands=bandsVal,
                    sampling=samplingVal,
                    kmMaxIter=kmMaxIterVal,
                    processInMem=False,
                    saveProcessStats=True,
                    imgStretchStats=strchStatsOutFile,
                    kMeansCentres=kCentresOutFile,
                    imgStatsJSONFile=tmpStatsJSON)
                print(" !!! finished the seg on tile " + imgTile)

            except:
                print(
                    " !&!" + imgTile +
                    " Error: Its likely this tile doesn't have enough of the geotiff inside its extent to run the seg algorithm. I recommend overlaying the tiling shapefile (..._S1Tiles.shp) on the geotiff to check the extents. You can't proceed further until you deal with this as Part 2 will fail."
                )
                pass

        with Pool(ncpus) as p:
            p.map(threadedTiledImgSeg, imgTiles)

        print("completed the stage 1 image seg")

    def defineStage1Boundaries(self, tilesImgDIR, stage1TilesSegBordersDIR,
                               tilesBase):
        segTiles = glob.glob(os.path.join(tilesImgDIR,
                                          tilesBase + "*_segs.kea"))
        for segTile in segTiles:
            baseName = os.path.splitext(os.path.basename(segTile))[0]
            borderMaskFile = os.path.join(stage1TilesSegBordersDIR,
                                          baseName + '_segsborder.kea')
            rastergis.defineBorderClumps(segTile, 'BoundaryClumps')
            rastergis.exportCol2GDALImage(segTile, borderMaskFile, 'KEA',
                                          rsgislib.TYPE_8UINT, 'BoundaryClumps')

    def mergeStage1TilesToOutput(self, inputImage, tilesSegsDIR,
                                 tilesSegsBordersDIR, tilesBase, clumpsImage,
                                 bordersImage):
        segTiles = glob.glob(
            os.path.join(tilesSegsDIR, tilesBase + "*_segs.kea"))
        imageutils.createCopyImage(inputImage, clumpsImage, 1, 0, 'KEA',
                                   rsgislib.TYPE_32UINT)
        segmentation.mergeClumpImages(segTiles, clumpsImage)
        rastergis.populateStats(clumpsImage, True, True)

        tileBorders = glob.glob(
            os.path.join(tilesSegsBordersDIR, tilesBase + "*_segsborder.kea"))
        imageutils.createCopyImage(inputImage, bordersImage, 1, 0, 'KEA',
                                   rsgislib.TYPE_8UINT)
        imageutils.includeImages(bordersImage, tileBorders)
        rastergis.populateStats(bordersImage, True, True)

    def performStage2Tiling(self, inputImage, tileShp, tilesRat, tilesBase,
                            tilesMetaDIR, tilesImgDIR, tmpDIR, width, height,
                            validDataThreshold, bordersImage):
        tilingutils.createMinDataTiles(inputImage, tileShp, tilesRat, width,
                                       height, validDataThreshold, bordersImage,
                                       True, True, tmpDIR)
        tilingutils.createTileMaskImagesFromClumps(tilesRat, tilesBase,
                                                   tilesMetaDIR, "KEA")
        rsgisUtils = rsgislib.RSGISPyUtils()
        dataType = rsgisUtils.getRSGISLibDataTypeFromImg(inputImage)
        tilingutils.createTilesFromMasks(inputImage, tilesBase, tilesMetaDIR,
                                         tilesImgDIR, dataType, 'KEA')

    def performStage2TilesSegmentation(self, tilesImgDIR, tilesMaskedDIR,
                                       tilesSegsDIR, tilesSegBordersDIR, tmpDIR,
                                       tilesBase, s1BordersImage, segStatsInfo,
                                       minPxlsVal, distThresVal, bandsVal,
                                       ncpus):
        rsgisUtils = rsgislib.RSGISPyUtils()
        imgTiles = glob.glob(os.path.join(tilesImgDIR, tilesBase + "*.kea"))
        for imgTile in imgTiles:
            baseName = os.path.splitext(os.path.basename(imgTile))[0]
            maskedFile = os.path.join(tilesMaskedDIR, baseName + '_masked.kea')
            dataType = rsgisUtils.getRSGISLibDataTypeFromImg(imgTile)
            imageutils.maskImage(imgTile, s1BordersImage, maskedFile, 'KEA',
                                 dataType, 0, 0)

        imgTiles = glob.glob(
            os.path.join(tilesMaskedDIR, tilesBase + "*_masked.kea"))

        def stage2threadedTiledImgSeg(imgTile):
            baseName = os.path.splitext(os.path.basename(imgTile))[0]
            clumpsFile = os.path.join(tilesSegsDIR, baseName + '_segs.kea')
            kMeansCentres, imgStretchStats = self.findSegStatsFiles(
                imgTile, segStatsInfo)
            segutils.runShepherdSegmentationPreCalcdStats(
                imgTile,
                clumpsFile,
                kMeansCentres,
                imgStretchStats,
                outputMeanImg=None,
                tmpath=os.path.join(tmpDIR, baseName + '_segstemp'),
                gdalformat='KEA',
                noStats=False,
                noStretch=False,
                noDelete=False,
                minPxls=minPxlsVal,
                distThres=distThresVal,
                bands=bandsVal,
                processInMem=False)

        p = Pool(ncpus)
        p.map(stage2threadedTiledImgSeg, imgTiles)

        segTiles = glob.glob(
            os.path.join(tilesSegsDIR, tilesBase + "*_segs.kea"))
        for segTile in segTiles:
            baseName = os.path.splitext(os.path.basename(segTile))[0]
            borderMaskFile = os.path.join(tilesSegBordersDIR,
                                          baseName + '_segsborder.kea')
            rastergis.defineBorderClumps(segTile, 'BoundaryClumps')
            rastergis.exportCol2GDALImage(segTile, borderMaskFile, 'KEA',
                                          rsgislib.TYPE_8UINT, 'BoundaryClumps')

    def mergeStage2TilesToOutput(self, clumpsImage, tilesSegsDIR,
                                 tilesSegBordersDIR, tilesBase, s2BordersImage):
        segTiles = glob.glob(
            os.path.join(tilesSegsDIR, tilesBase + "*_segs.kea"))
        segmentation.mergeClumpImages(segTiles, clumpsImage)
        rastergis.populateStats(clumpsImage, True, True)

        tileBorders = glob.glob(
            os.path.join(tilesSegBordersDIR, tilesBase + "*_segsborder.kea"))
        imageutils.createCopyImage(clumpsImage, s2BordersImage, 1, 0, 'KEA',
                                   rsgislib.TYPE_8UINT)
        imageutils.includeImages(s2BordersImage, tileBorders)

    def createStage3ImageSubsets(self, inputImage, s2BordersImage,
                                 s3BordersClumps, subsetImgsDIR,
                                 subsetImgsMaskedDIR, subImgBaseName, minSize):
        segmentation.clump(s2BordersImage, s3BordersClumps, 'KEA', True, 0)
        rastergis.populateStats(s3BordersClumps, True, True)

        rastergis.spatialExtent(s3BordersClumps, 'minXX', 'minXY', 'maxXX',
                                'maxXY', 'minYX', 'minYY', 'maxYX', 'maxYY')

        rsgisUtils = rsgislib.RSGISPyUtils()
        dataType = rsgisUtils.getRSGISLibDataTypeFromImg(inputImage)

        ratDS = gdal.Open(s3BordersClumps, gdal.GA_Update)
        minX = rat.readColumn(ratDS, "minXX")
        maxX = rat.readColumn(ratDS, "maxXX")
        minY = rat.readColumn(ratDS, "minYY")
        maxY = rat.readColumn(ratDS, "maxYY")
        Histogram = rat.readColumn(ratDS, "Histogram")
        for i in range(minX.shape[0]):
            if i > 0:
                subImage = os.path.join(subsetImgsDIR,
                                        subImgBaseName + str(i) + '.kea')
                #print( "[" + str(minX[i]) + ", " + str(maxX[i]) + "][" + str(minY[i]) + ", " + str(maxY[i]) + "]" )
                imageutils.subsetbbox(inputImage, subImage, 'KEA', dataType,
                                      minX[i], maxX[i], minY[i], maxY[i])
                if Histogram[i] > minSize:
                    maskedFile = os.path.join(
                        subsetImgsMaskedDIR,
                        subImgBaseName + str(i) + '_masked.kea')
                else:
                    maskedFile = os.path.join(
                        subsetImgsMaskedDIR,
                        subImgBaseName + str(i) + '_burn.kea')
                imageutils.maskImage(subImage, s2BordersImage, maskedFile,
                                     'KEA', dataType, 0, 0)
                rastergis.populateStats(maskedFile, True, False)
        ratDS = None

    def performStage3SubsetsSegmentation(self, subsetImgsMaskedDIR,
                                         subsetSegsDIR, tmpDIR, subImgBaseName,
                                         segStatsInfo, minPxlsVal, distThresVal,
                                         bandsVal, ncpus):
        imgTiles = glob.glob(
            os.path.join(subsetImgsMaskedDIR, subImgBaseName + "*_masked.kea"))

        def stage3threadedTiledImgSeg(imgTile):
            baseName = os.path.splitext(os.path.basename(imgTile))[0]
            clumpsFile = os.path.join(subsetSegsDIR, baseName + '_segs.kea')
            kMeansCentres, imgStretchStats = self.findSegStatsFiles(
                imgTile, segStatsInfo)
            segutils.runShepherdSegmentationPreCalcdStats(
                imgTile,
                clumpsFile,
                kMeansCentres,
                imgStretchStats,
                outputMeanImg=None,
                tmpath=os.path.join(tmpDIR, baseName + '_segstemp'),
                gdalformat='KEA',
                noStats=False,
                noStretch=False,
                noDelete=False,
                minPxls=minPxlsVal,
                distThres=distThresVal,
                bands=bandsVal,
                processInMem=False)

        p = Pool(ncpus)
        p.map(stage3threadedTiledImgSeg, imgTiles)

    def mergeStage3TilesToOutput(self, clumpsImage, subsetSegsDIR,
                                 subsetImgsMaskedDIR, subImgBaseName):
        burnTiles = glob.glob(
            os.path.join(subsetImgsMaskedDIR, subImgBaseName + "*_burn.kea"))
        if len(burnTiles) > 0:
            segmentation.mergeClumpImages(burnTiles, clumpsImage)

        segTiles = glob.glob(
            os.path.join(subsetSegsDIR, subImgBaseName + "*_segs.kea"))
        segmentation.mergeClumpImages(segTiles, clumpsImage)
        rastergis.populateStats(clumpsImage, True, True)


def performTiledSegmentation(inputImage,
                             clumpsImage,
                             tmpDIR='segtmp',
                             tileWidth=2000,
                             tileHeight=2000,
                             validDataThreshold=0.3,
                             numClusters=60,
                             minPxls=100,
                             distThres=100,
                             bands=None,
                             sampling=100,
                             kmMaxIter=200,
                             ncpus=1):
    """
    Utility function to call the segmentation algorithm of Shepherd et al. (2014)
    using the tiled process outlined in Clewley et al (2015). Adapted here to run tiles
    across multiple cpus. Use this function to conduct image segmentation on very large
    geotiffs.

    Parameters
    ----------
    inputImage : str
        is a string containing the name of the input file.
    clumpsImage : str
        is a string containing the name of the output clump file.
    tmpath : str 
        is a file path for intermediate files (default is to create a directory 'segtmp').
        If path does current not exist then it will be created and deleted afterwards.
    tileWidth : int
        is an int specifying the width of the tiles used for processing (Default 2000)
    tileHeight : int
        is an int specifying the height of the tiles used for processing (Default 2000)
    validDataThreshold : float
        is a float (value between 0 - 1) used to specify the amount of valid image
        pixels (i.e., not a no data value of zero) are within a tile. Tiles failing to meet this
        threshold are merged with ones which do (Default 0.3).
    numClusters : int 
        is an int which specifies the number of clusters within the KMeans clustering (default = 60).
    minPxls : int
        is an int which specifies the minimum number pixels within a segments (default = 100).
    distThres : int 
        specifies the distance threshold for joining the segments (default = 100, set to large number to turn off this option).
    bands : array-like
        is an array providing a subset of image bands to use (default is None to use all bands).
    sampling : 
        specify the subsampling of the image for the data used within the KMeans (default = 100; 1 == no subsampling).
    kmMaxIter : 
        maximum iterations for KMeans (Default 200).

    Returns
    -------
    Segmented .kea file stored on disk at the location of 'clumpsImage'
    
    """
    createdTmp = False
    if not os.path.exists(tmpDIR):
        os.makedirs(tmpDIR)
        createdTmp = True
    rsgisUtils = rsgislib.RSGISPyUtils()
    uidStr = rsgisUtils.uidGenerator()

    baseName = os.path.splitext(os.path.basename(inputImage))[0] + "_" + uidStr

    tileSegInfo = os.path.join(tmpDIR, baseName + '_seginfo.json')
    segStatsDIR = os.path.join(tmpDIR, 'segStats_' + uidStr)
    strchStatsBase = os.path.join(segStatsDIR, baseName + '_stch')
    kCentresBase = os.path.join(segStatsDIR, baseName + '_kcentres')
    if not os.path.exists(segStatsDIR):
        os.makedirs(segStatsDIR)

    tiledSegObj = RSGISTiledShepherdSegmentationSingleThread()

    ######################## STAGE 1 #######################
    # Stage 1 Parameters (Internal)
    stage1TileShp = os.path.join(tmpDIR, baseName + '_S1Tiles.shp')
    stage1TileRAT = os.path.join(tmpDIR, baseName + '_S1Tiles.kea')
    stage1TilesBase = baseName + '_S1Tile'
    stage1TilesImgDIR = os.path.join(tmpDIR, 's1tilesimgs_' + uidStr)
    stage1TilesMetaDIR = os.path.join(tmpDIR, 's1tilesmeta_' + uidStr)
    stage1TilesSegsDIR = os.path.join(tmpDIR, 's1tilessegs_' + uidStr)
    stage1TilesSegBordersDIR = os.path.join(tmpDIR,
                                            's1tilessegborders_' + uidStr)
    stage1BordersImage = os.path.join(tmpDIR, baseName + '_S1Borders.kea')

    if not os.path.exists(stage1TilesImgDIR):
        os.makedirs(stage1TilesImgDIR)
    if not os.path.exists(stage1TilesSegsDIR):
        os.makedirs(stage1TilesSegsDIR)
    if not os.path.exists(stage1TilesSegBordersDIR):
        os.makedirs(stage1TilesSegBordersDIR)
    if not os.path.exists(stage1TilesMetaDIR):
        os.makedirs(stage1TilesMetaDIR)

    # Initial Tiling
    tiledSegObj.performStage1Tiling(inputImage, stage1TileShp, stage1TileRAT,
                                    stage1TilesBase, stage1TilesMetaDIR,
                                    stage1TilesImgDIR,
                                    os.path.join(tmpDIR, 's1tilingtemp'),
                                    tileWidth, tileHeight, validDataThreshold)

    # Perform Segmentation
    print('Performing Stage 1 seg...multithreaded with ' + str(ncpus) + " cpus")
    tiledSegObj.performStage1TilesSegmentation(
        stage1TilesImgDIR, stage1TilesSegsDIR, tmpDIR, stage1TilesBase,
        tileSegInfo, strchStatsBase, kCentresBase, numClusters, minPxls,
        distThres, bands, sampling, kmMaxIter, ncpus)

    # grab the stats for each tile and add to json
    tileStatsFiles = dict()
    for file in os.listdir(stage1TilesImgDIR):
        if file.endswith(".json"):
            baseName = os.path.splitext(os.path.basename(file))[0][:-9]
            with open(stage1TilesImgDIR + "/" + file, 'r') as f:
                jsonStrData = f.read()
            segStatsInfo = json.loads(jsonStrData)
            tileStatsFiles[baseName] = segStatsInfo

    with open(tileSegInfo, 'w') as outfile:
        json.dump(tileStatsFiles,
                  outfile,
                  sort_keys=True,
                  indent=4,
                  separators=(',', ': '),
                  ensure_ascii=False)

    # Define Boundaries
    print('defining stage 1 boundaries')
    tiledSegObj.defineStage1Boundaries(stage1TilesSegsDIR,
                                       stage1TilesSegBordersDIR,
                                       stage1TilesBase)

    print('Merging stage 1 segmented tiles')
    # Merge the Initial Tiles
    tiledSegObj.mergeStage1TilesToOutput(inputImage, stage1TilesSegsDIR,
                                         stage1TilesSegBordersDIR,
                                         stage1TilesBase, clumpsImage,
                                         stage1BordersImage)

    shutil.rmtree(stage1TilesImgDIR)
    shutil.rmtree(stage1TilesSegsDIR)
    shutil.rmtree(stage1TilesSegBordersDIR)
    shutil.rmtree(stage1TilesMetaDIR)
    ########################################################

    with open(tileSegInfo, 'r') as f:
        jsonStrData = f.read()
    segStatsInfo = json.loads(jsonStrData)

    ######################## STAGE 2 #######################
    # Stage 2 Parameters (Internal)
    stage2TileShp = os.path.join(tmpDIR, baseName + '_S2Tiles.shp')
    stage2TileRAT = os.path.join(tmpDIR, baseName + '_S2Tiles.kea')
    stage2TilesBase = baseName + '_S2Tile'
    stage2TilesImgDIR = os.path.join(tmpDIR, 's2tilesimg_' + uidStr)
    stage2TilesMetaDIR = os.path.join(tmpDIR, 's2tilesmeta_' + uidStr)
    stage2TilesImgMaskedDIR = os.path.join(tmpDIR, 's2tilesimgmask_' + uidStr)
    stage2TilesSegsDIR = os.path.join(tmpDIR, 's2tilessegs_' + uidStr)
    stage2TilesSegBordersDIR = os.path.join(tmpDIR,
                                            's2tilessegborders_' + uidStr)
    stage2BordersImage = os.path.join(tmpDIR, baseName + '_S2Borders.kea')

    if not os.path.exists(stage2TilesImgDIR):
        os.makedirs(stage2TilesImgDIR)
    if not os.path.exists(stage2TilesMetaDIR):
        os.makedirs(stage2TilesMetaDIR)
    if not os.path.exists(stage2TilesImgMaskedDIR):
        os.makedirs(stage2TilesImgMaskedDIR)
    if not os.path.exists(stage2TilesSegsDIR):
        os.makedirs(stage2TilesSegsDIR)
    if not os.path.exists(stage2TilesSegBordersDIR):
        os.makedirs(stage2TilesSegBordersDIR)

    # Perform offset tiling
    print('Performing stage2 offset tilings')
    tiledSegObj.performStage2Tiling(inputImage, stage2TileShp, stage2TileRAT,
                                    stage2TilesBase, stage2TilesMetaDIR,
                                    stage2TilesImgDIR,
                                    os.path.join(tmpDIR, 's2tilingtemp'),
                                    tileWidth, tileHeight, validDataThreshold,
                                    stage1BordersImage)

    print('Performing segmentation of stage2 offset tiles')
    # Perform Segmentation of the Offset Tiles
    tiledSegObj.performStage2TilesSegmentation(
        stage2TilesImgDIR, stage2TilesImgMaskedDIR, stage2TilesSegsDIR,
        stage2TilesSegBordersDIR, tmpDIR, stage2TilesBase, stage1BordersImage,
        segStatsInfo, minPxls, distThres, bands, ncpus)

    # Merge in the next set of boundaries
    print('merging next set of boundaries')
    tiledSegObj.mergeStage2TilesToOutput(clumpsImage, stage2TilesSegsDIR,
                                         stage2TilesSegBordersDIR,
                                         stage2TilesBase, stage2BordersImage)

    shutil.rmtree(stage2TilesImgDIR)
    shutil.rmtree(stage2TilesMetaDIR)
    shutil.rmtree(stage2TilesImgMaskedDIR)
    shutil.rmtree(stage2TilesSegsDIR)
    shutil.rmtree(stage2TilesSegBordersDIR)
    ########################################################

    ######################## STAGE 3 #######################
    print('starting stage 3')
    # Stage 3 Parameters (Internal)
    stage3BordersClumps = os.path.join(tmpDIR,
                                       baseName + '_S3BordersClumps.kea')
    stage3SubsetsDIR = os.path.join(tmpDIR, 's3subsetimgs_' + uidStr)
    stage3SubsetsMaskedDIR = os.path.join(tmpDIR, 's3subsetimgsmask_' + uidStr)
    stage3SubsetsSegsDIR = os.path.join(tmpDIR, 's3subsetsegs_' + uidStr)
    stage3Base = baseName + '_S3Subset'

    if not os.path.exists(stage3SubsetsDIR):
        os.makedirs(stage3SubsetsDIR)
    if not os.path.exists(stage3SubsetsMaskedDIR):
        os.makedirs(stage3SubsetsMaskedDIR)
    if not os.path.exists(stage3SubsetsSegsDIR):
        os.makedirs(stage3SubsetsSegsDIR)

    # Create the final boundary image subsets
    print('creating final image subsets')
    tiledSegObj.createStage3ImageSubsets(inputImage, stage2BordersImage,
                                         stage3BordersClumps, stage3SubsetsDIR,
                                         stage3SubsetsMaskedDIR, stage3Base,
                                         minPxls)

    # Perform Segmentation of the stage 3 regions
    print("Performing Segmentation of the stage 3 regions")
    tiledSegObj.performStage3SubsetsSegmentation(stage3SubsetsMaskedDIR,
                                                 stage3SubsetsSegsDIR, tmpDIR,
                                                 stage3Base, segStatsInfo,
                                                 minPxls, distThres, bands,
                                                 ncpus)

    # Merge the stage 3 regions into the final clumps image
    print('merging stage 3 regions into the final clumps image')
    tiledSegObj.mergeStage3TilesToOutput(clumpsImage, stage3SubsetsSegsDIR,
                                         stage3SubsetsMaskedDIR, stage3Base)

    shutil.rmtree(stage3SubsetsDIR)
    shutil.rmtree(stage3SubsetsMaskedDIR)
    shutil.rmtree(stage3SubsetsSegsDIR)
    ########################################################

    shutil.rmtree(segStatsDIR)
    rsgisUtils = rsgislib.RSGISPyUtils()
    rsgisUtils.deleteFileWithBasename(stage1BordersImage)
    rsgisUtils.deleteFileWithBasename(stage2BordersImage)
    rsgisUtils.deleteFileWithBasename(stage3BordersClumps)
    rsgisUtils.deleteFileWithBasename(stage1TileShp)
    rsgisUtils.deleteFileWithBasename(stage1TileRAT)
    rsgisUtils.deleteFileWithBasename(stage2TileShp)
    rsgisUtils.deleteFileWithBasename(stage2TileRAT)
    os.remove(tileSegInfo)
    if createdTmp:
        shutil.rmtree(tmpDIR)
    print('Done!')
