def transform_tuple(ds, coords, epsg=3577, rotation=0.0):
    """
    Creates a transform tuple from an xarray object for use with GDAL, along with
    a projection object in the form of WKT.

    ds = xarray dataset or dataArray
    coords = tuple. The georeferencing coordinate data. e.g (ds.long,ds.lat) or (ds.x,ds.y)
                    Order MUST BE X then Y
    epsg = int. a projection in epsg format
    rotation = the degrees of rotation of the image. If North up, rotation = 0.0
    
    """
    east = float(coords[0][0])
    EW_pixelRes = float(coords[1][0] - coords[1][1])
    north = float(coords[1][0])
    NS_pixelRes = float(coords[0][0] - coords[0][1])        

    transform = (east, EW_pixelRes, rotation, north, rotation, NS_pixelRes)
    
    import osr
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    prj_wkt = srs.ExportToWkt()
    
    return transform, prj_wkt
