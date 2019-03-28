def reproject_image_to_master ( master, slave, res=None ):
    """This function reprojects an image (``slave``) to
    match the extent, resolution and projection of another
    (``master``) using GDAL. The newly reprojected image
    is a GDAL VRT file for efficiency. A different spatial
    resolution can be chosen by specifyign the optional
    ``res`` parameter. The function returns the new file's
    name.
    Parameters
    -------------
    master: str 
        A filename (with full path if required) with the 
        master image (that that will be taken as a reference)
    slave: str 
        A filename (with path if needed) with the image
        that will be reprojected
    res: float, optional
        The desired output spatial resolution, if different 
        to the one in ``master``.
    Returns
    ----------
    The reprojected filename
    TODO Have a way of controlling output filename
    """
    from osgeo import gdal
    slave_ds = gdal.Open( slave )
    slave_proj = slave_ds.GetProjection()
    slave_geotrans = slave_ds.GetGeoTransform()
    data_type = slave_ds.GetRasterBand(1).DataType
    n_bands = slave_ds.RasterCount

    master_ds = gdal.Open( master )

    master_proj = master_ds.GetProjection()
    master_geotrans = master_ds.GetGeoTransform()
    w = master_ds.RasterXSize
    h = master_ds.RasterYSize
    if res is not None:
        master_geotrans[1] = float( res )
        master_geotrans[-1] = - float ( res )

    dst_filename = slave.replace( ".tif", "_crop.tif" )
    dst_ds = gdal.GetDriverByName('GTiff').Create(dst_filename,
                                                w, h, n_bands, data_type)
    dst_ds.SetGeoTransform( master_geotrans )
    dst_ds.SetProjection( master_proj)

    gdal.ReprojectImage( slave_ds, dst_ds, slave_proj,
                         master_proj, gdal.GRA_NearestNeighbour)
    dst_ds = None  # Flush to disk
    return dst_filename