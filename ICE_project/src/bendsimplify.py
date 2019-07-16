
#-------------------------------------------------------------------------------
# Name:         bendsimplify.py
# Purpose:      bend simplify based on bezier curves.
#-------------------------------------------------------------------------------
import sys
import os
import time
import copy

from shapely.geometry import asShape
from shapely.geometry import MultiLineString
from shapely.geometry import asLineString
from shapely.wkt import dumps
#from pprint import pprint

import shapefile
import bezier
import numpy as np

# READ IN SHAPEFILE DATA -------------------------------------------------------
def bend_simplify(shp_file):

    startTime = time.time()

    sf_source = shapefile.Reader(shp_file) # shapefile source
    flds = [header[0] for header in sf_source.fields[1:]] # fields, gets rid of deletion()
    objID = flds.index("OBJECTID")

    # EXTRACT OBJECT IDS OF NEIGHBORING POLYGONS -----------------------------------

    # get all the object ids and convert shapes to shapely geometry
    oids = [row[objID] for row in sf_source.iterRecords()]
    geom = [asShape(shape) for shape in sf_source.iterShapes()]

    # store records and shapely geometry based on object ids as dictionaries
    recByOid = {row[objID]:row for row in sf_source.iterRecords()}
    geomsDict = dict(zip(oids, geom))

    # create an empty dictionary to store ids & common border of adjacent polygons
    adjPolyID = {item:[] for item in oids} # to store object id's

    # now iterate through the features (geom) and check for intersection
    for i in range(len(geom)):
        for j in range(len(geom)):
            # check to see if features intersect while avoiding self intersection
            if geom[i].intersects(geom[j]) == True and i != j:
                adjPolyID[oids[i]].append(oids[j])

    # EXTRACT COMMON BORDERS -------------------------------------------------------
    # we only need common borders that are not duplicates thus store intersects only
    # SO we get rid of duplicates since A^B == B^A i.e. (^ = intersect)

    geomByOid = copy.deepcopy(adjPolyID) # make deep copy of all neighbor polygon id's

    for ks,vs in geomByOid.iteritems():
        print(ks, vs)
        for v in vs:
               if ks in geomByOid[v]:
                   geomByOid[v].remove(ks)

    # Loop through adjacent poly dictionary and for each object id, get the feature,
    # perfrom an intersection. (a)BUT 1st eliminate [] values created by geomByOid

    geomByOidNotNull = {item:vals for item,vals in geomByOid.iteritems() if vals != []}
    print("Neighbors for {} are {}".format(oids[0], geomByOidNotNull[oids[0]]))

    # (b) create empty value keys for populating with common border intersections
    adjPolyBord = {item:[] for item in geomByOidNotNull}

    # (c) actual iteration
    for ks,vs in geomByOidNotNull.iteritems():
        for v in vs:
            # get intersection for key feature and each value feature where values not null
            border = geomsDict[ks].intersection(geomsDict[v])
            adjPolyBord[ks].append(border)

    # perform some simple tests (i.e. no null values), also get a length
    print("Length of {} intersect {} is {}".format(oids[0], geomByOidNotNull[oids[0]][0], adjPolyBord[oids[0]][0].length))

    # Loop through each common border stored as values in adjPolyBord dictionary
    # Noting that for shapely, intersections could result in geometric collections.
    # Here i opted to convert the intersections to MultiLinestring

    # test to identify existing geometries from intersections. I found Polygons & Linestrings

    adjPolyBordSameGeom = {oid:[] for oid in adjPolyBord} # to hold same geometry intersections

    for ks,vs in adjPolyBord.iteritems():
        for v in vs:
            # convert linestrings hidden in geometry collection to multiline strings
            if v.geom_type=="GeometryCollection":
                points = []
                for feat in v:
                    if feat.geom_type=="LineString":
                        points.append(feat.coords)
                    else:
                        points.append(feat.boundary.coords) # boundary of polygon is linestring
                adjPolyBordSameGeom[ks].append(MultiLineString(points))

            else:
                adjPolyBordSameGeom[ks].append(v)

    # EXTRACT EXTERNAL BORDERS------------------------------------------------------

    # get external borders based on info from internal borders
    disjPolyID = [ks for ks in adjPolyID] # List of all polygons by their ID
    aPBSGList = [item for sublist in adjPolyBordSameGeom.itervalues() for item in sublist] # or adjPolyBord.itervalues()
    disjPolyBord = {k:v.boundary for k,v in geomsDict.items()} # get features as multilinestrings

    for ks in disjPolyID:
        for comBord in aPBSGList:
            if comBord.intersects(geomsDict[ks]):
                disjPolyBord[ks] = disjPolyBord[ks].difference(comBord)

    # BEND SIMPLIFY THE BORDERS-----------------------------------------------------

    # a) create a list of all the borders so that we loop through them and simplify
    allBorders = aPBSGList + [val for val in disjPolyBord.itervalues()]

    # b) actual bend simplification
    minHalfCircleBend = 2000 # start with 3 kilometer based on my selection of polygons

    bendedLines = []
    for lines in allBorders:

        if lines.geom_type=="MultiLineString":
            newMultiLine = []
            #print "Number of lines in this feature ", len(lines)
            for line in lines:
                points = np.array(line) # convert linestring to array
                minHalfCircleBendArray = []
                pntCounter = 1
                start = 0
                nPoints = len(points)
                disTot = 0
                midPointList = []
                newPointList = [[0,0], [0,0]]

                # add the first point of the polygon (in this case linear ring)
                newPointList = np.concatenate((newPointList, [points[0]]), 0)
                newPointList = np.delete(newPointList, [0,1], 0)

                # loop through each of the points
                for point in points:
                    if pntCounter < nPoints:
                        # compare points distance
                        dist = np.linalg.norm(points[start] - points[pntCounter])
                         # collect points if dist is less than minhalf circle bend
                        if (dist + disTot) <= minHalfCircleBend:
                            disTot += dist
                            midPointList.append(points[pntCounter])
                        elif (pntCounter - start <= 1):
                            # for neighboring points, get a straight line
                            newPointList = np.concatenate((newPointList, [points[pntCounter]]))
                        else:
                            # calculate bezier, not sure where to use minimumArea
                            triangleArea = 0
                            bezMidPoint = point
                            for midpoint in midPointList:
                                a = dist
                                b = np.linalg.norm(points[start] - midpoint)
                                c = np.linalg.norm(midpoint - points[pntCounter])
                                s = 0.5 * (a + b + c)
                                area = np.sqrt(s*(s-a)*(s-b)*(s-c))
                                if area > triangleArea:
                                    # save midpoint for bezier
                                    bezMidPoint = midpoint
                                    triangleArea = area

                            midPointList = []
                            xList = np.array([points[start][0], bezMidPoint[0], points[pntCounter][0]])
                            yList = np.array([points[start][1], bezMidPoint[1], points[pntCounter][1]])
                            start = pntCounter
                            bezCurve = bezier.bezier(xList, yList)
                            # add interpolated points to newpoints list
                            newPointList = np.concatenate((newPointList, bezCurve), 0)
                            disTot = 0
                            del bezCurve, xList, yList, bezMidPoint
                        pntCounter += 1

                    else:
                        newPointList = np.concatenate((newPointList, [points[pntCounter-1]]), 0) # for lines consider removing this as it always closes it?

                newLinestring = asLineString(newPointList) # could also use linear rings

                newMultiLine.append(newLinestring)

            bendedLines.append(MultiLineString(newMultiLine[0:]))

        elif lines.geom_type == "LineString":
            try:
                xList = [point[0] for point in linemerge(lines).coords]
                yList = [point[1] for point in linemerge(lines).coords]
                bezCurve = bezier.bezier(xList, yList)
                bendedLines.append(asLineString(bezCurve))
            except:
                pointReduce = lines.simplify(minHalfCircleBend) # just reduce the points
                bendedLines.append(pointReduce)

    # check if anything has happened, i.e. there should be a difference in lengths

    print("Length before simplification: ", allBorders[8].length) # can vary 8
    print("Length after simplification: ", bendedLines[8].length)

    # WRITE SIMPLIFIED BORDERS TO SHAPEFILE ----------------------------------------
    # (a) create a folder for output in script directory
    folder = "bendOutput"
    if os.path.exists(folder):
        import shutil
        shutil.rmtree(folder)
    if not os.path.exists(folder):
        os.makedirs(folder)

    from osgeo import ogr, osr

    driver = ogr.GetDriverByName("Esri Shapefile")
    ds = driver.CreateDataSource(folder + "/bendTest.shp")

    sp = osr.SpatialReference()
    sp.ImportFromEPSG(3395) # can be changed to any coord system

    layer = ds.CreateLayer(folder + "/bendTest", sp, ogr.wkbLineString)
    feature = ogr.Feature(layer.GetLayerDefn())

    for bend in bendedLines:
        feature.SetGeometry(ogr.CreateGeometryFromWkb(bend.wkb))
        layer.CreateFeature(feature)


    ds = layer = feature = None

    # HOW LONG IT TOOK
    endTime = time.time()
    timeDiff = endTime - startTime

    print("it took {:.1f} seconds".format(timeDiff))
