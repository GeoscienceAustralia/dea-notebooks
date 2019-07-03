
def geotransform(ds, coords, epsg=3577, alignment = 'centre', rotation=0.0):
    """
    Creates a GDAL geotransform tuple from an xarray object, along with
    a projection object in the form of WKT. Basically provides everything you need to use
    the 'array_to_geotiff' function from '10_Scripts/SpatialTools', and that is the express
    purpose for this function.
    
    :param ds:
        xarray dataset or dataArray object
    :param coords:
        Tuple. The georeferencing coordinate data in the xarray object. 
        e.g (ds.long,ds.lat) or (ds.x,ds.y). Order MUST BE X then Y
    :param epsg:
        Integer. A projection number in epsg format, defaults to 3577 (albers equal area).
    :param pixelSize:
        float. The size of the pixels in metres. defaults to 25m, as per Landsat pixel size
    :param alignment:
        Str. How should the coords be aligned with respect to the pixels? 
        If "centre", then the transform will align coordinates with the centre of the pixel.
        If 'upper_left', then coords will be aligned with the upperleftmost corner of array
    :param rotation:
        Float. the degrees of rotation of the image. If North is up, rotation = 0.0.
    
        Example:

        #Open an xarray object
        ds = xr.open_rasterio(input_file.tif).squeeze()

        #grab the trasnform and projection info from the dataset
        transform, projection = geotransform(ds, (ds.x, ds.y), epsg=3577)

        #use the transform object in a 'array_to_geotiff' function
        width,height = a.shape
        SpatialTools.array_to_geotiff("output_file.tif",
          ds.values, geo_transform = transform, 
          projection = projection, 
          nodata_val=-999)
    
      :Returns:
          A tuple containing the geotransform tuple and WKT projection information
          i.e. (transform_tuple, projection)
      -------------------------------------------------------------------------    
    """
    print("This function is written for use with the GDAL backed 'array_to_geotiff' function and should be used with extreme caution elsewhere.")
    
    
    if alignment == 'centre':
        EW_pixelRes = float(coords[1][0] - coords[1][1])
        NS_pixelRes = float(coords[0][0] - coords[0][1])        
        east = float(coords[0][0]) - (EW_pixelRes/2)
        north = float(coords[1][0]) + (NS_pixelRes/2)
        
        transform = (east, EW_pixelRes, rotation, north, rotation, NS_pixelRes)
    
    elif alignment == 'upper_left':
        EW_pixelRes = float(coords[1][0] - coords[1][1])
        NS_pixelRes = float(coords[0][0] - coords[0][1])        
        east = float(coords[0][0])
        north = float(coords[1][0])
        
        transform = (east, EW_pixelRes, rotation, north, rotation, NS_pixelRes)
    
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    prj_wkt = srs.ExportToWkt()
    
    return transform, prj_wkt
