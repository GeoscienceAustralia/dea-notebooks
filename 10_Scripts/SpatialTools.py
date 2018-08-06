# SpatialTools.py
"""
This file contains a set of python functions for manipulating rasters and shapefiles that do not 
specifically rely on DEA functionality (i.e. no dc.load or xarrays)

Available functions:

    rasterize_vector
    layer_extent
    indices_to_coords
    coords_to_indices
    raster_randomsample
    array_to_geotiff
    reproject_to_template

Last modified: April 2018
Author: Robbi Bishop-Taylor

"""

import gdal
import numpy as np


def rasterize_vector(input_data, cols, rows, geo_transform, projection, 
                     field=None, raster_path=None, array_dtype=gdal.GDT_UInt16):
    """
    Rasterize a vector file and return an array with values for cells that occur within the 
    shapefile. Can be used to obtain a binary array (shapefile vs no shapefile), or can create 
    an array containing values from a shapefile field. If 'raster_path' is provided, the 
    resulting array can also be output as a geotiff raster.
    
    This function requires dimensions, projection data (in 'WKT' format) and geotransform info 
    ('(upleft_x, x_size, x_rotation, upleft_y, y_rotation, y_size)') for the output array. 
    These are typically obtained from an existing raster using the following GDAL calls:
    
    >>> import gdal
    >>> gdal_dataset = gdal.Open(raster_path)
    >>> out_array = gdal_dataset.GetRasterBand(1).ReadAsArray() 
    >>> geo_transform = gdal_dataset.GetGeoTransform()
    >>> projection = gdal_dataset.GetProjection()
    >>> cols, rows = out_array.shape
    
    Last modified: April 2018
    Author: Robbi Bishop-Taylor

    :param input_data: 
        Input shapefile path or preloaded GDAL/OGR layer. This must be in the same 
        projection system as the desired output raster (i.e. same as the 'projection'
        parameter below)
        
    :param cols: 
        Desired width of output array in columns. This can be obtained from 
        an existing array using '.shape[0]'
        
    :param rows: 
        Desired height of output array in rows. This can be obtained from 
        an existing array using '.shape[1]'
        
    :param geo_transform: 
        Geotransform for output raster; e.g. "(upleft_x, x_size, x_rotation, 
        upleft_y, y_rotation, y_size)"
        
    :param projection: 
        Projection for output raster (in "WKT" format). This must be the same as the 
        input shapefile's projection system (i.e. same projection as used by 'input_data')
        
    :param field: 
        Shapefile field to rasterize values from. If None (default), this assigns a 
        value of 1 to all array cells within the shapefile, and 0 to areas outside 
        the shapefile
        
    :param raster_path: 
        If a path is supplied, the resulting array will also be output as a geotiff raster. 
        (defaults to None, which returns only the output array and does not write a file) 
        
    :param array_dtype: 
        Optionally set the dtype of the output array. This defaults to integers 
        (gdal.GDT_UInt16), and should only be changed if rasterising float values from a 
        shapefile field

    :return: 
        A 'row x col' array containing values from vector (if Field is supplied), or binary 
        values (1=shapefile data, 0=no shapefile)        
        
    """

    # If input data is a string, import as shapefile layer
    if isinstance(input_data, str):
        
        # Open vector with gdal
        data_source = gdal.OpenEx(input_data, gdal.OF_VECTOR)
        input_data = data_source.GetLayer(0)

    # If raster path supplied, save rasterized file as a geotiff
    if raster_path:

        # Set up output raster
        print('Exporting raster to {}'.format(raster_path))
        driver = gdal.GetDriverByName('GTiff')
        target_ds = driver.Create(raster_path, cols, rows, 1, array_dtype)

    else:

        # If no raster path, create raster as memory object
        driver = gdal.GetDriverByName('MEM')  # In memory dataset
        target_ds = driver.Create('', cols, rows, 1, array_dtype)

    # Set geotransform and projection
    target_ds.SetGeoTransform(geo_transform)
    target_ds.SetProjection(projection)

    # Rasterize shapefile and extract array using field if supplied; else produce binary array
    if field:
        
        # Rasterise by taking attributes from supplied
        gdal.RasterizeLayer(target_ds, [1], input_data, options=["ATTRIBUTE=" + field])
        
    else:
        
        # Rasterise into binary raster (1=shapefile data, 0=no shapefile)
        gdal.RasterizeLayer(target_ds, [1], input_data)    
    
    # Return array from raster
    band = target_ds.GetRasterBand(1)
    out_array = band.ReadAsArray()
    target_ds = None

    return out_array


def layer_extent(layer):
    """
    Computes min and max extents from GDAL layer features. Compared to
    built-in ".GetExtent" that always calculates extents on unfiltered layers,
    this allows you to compute extents of features in layers filtered with
    'SetAttributeFilter'. Works for point, line and polygon features, returning
    the extent of feature centroids for lines and polygon datasets.
    
    Last modified: March 2018
    Author: Robbi Bishop-Taylor

    :param layer: 
        Shapefile imported as GDAL layer; e.g.        
        >>> data_source = gdal.OpenEx(train_shp, gdal.OF_VECTOR)
        >>> layer = data_source.GetLayer(0)

    :return: 
        Min and max extent in x and y direction
    """

    # Extract tuples of x, y, z coordinates for each point feature
    point_coords = [feature.geometry().Centroid().GetPoint() for feature in layer]

    # Compute mins and maxes across points for each tuple element
    max_x, max_y, max_z = map(min, zip(*point_coords))
    min_x, min_y, min_z = map(max, zip(*point_coords))

    return min_x, max_x, min_y, max_y


def indices_to_coords(x_inds, y_inds, input_raster):
    
    """
    Takes lists of x and y array indices and converts them to corresponding spatial x and y 
    coordinates. For example, the very top-left cell of a raster's array will have indices (0, 0), but 
    when converted to spatial coordinates this cell location may be equivelent to a point with XXX.00 
    longitude, -XX.00 latitude. 
    
    This function can be used to identify the real-world spatial coordinates of raster cells meeting 
    certain criteria, i.e.:
    
    >>> raster_path = "test.tif"    
    >>> raster_ds = gdal.Open(raster_path)
    >>> raster_array = raster_ds.GetRasterBand(1).ReadAsArray()
    >>> y_inds, x_inds = np.nonzero(raster_array > 50)  # this computes indices of cells that are not 0
    >>> indices_to_coords(x_inds=x_inds, x_inds=y_inds, input_raster=raster_path)
    
    Last modified: April 2018
    Author: Robbi Bishop-Taylor
    
    :param x_inds: 
        List of x indices corresponding to a set of raster array cells
        
    :param y_inds: 
        List of y indices corresponding to a set of raster array cells
        
    :param input_raster: 
        Path to raster used to convert x and y indices from an array into spatial coordinates
                            
    :return x_coords: 
        List of spatial x coordinates corresponding to the location of raster array x cell 
        indices; coordinates will be in the projection system of input_raster
        
    :return y_coords: 
        List of spatial y coordinates corresponding to the location of raster array y cell 
        indices; coordinates will be in the projection system of input_raster
    """
    
    # Import raster
    raster_ds = gdal.Open(input_raster)
    raster_array = raster_ds.GetRasterBand(1).ReadAsArray() 
    raster_rows, raster_cols = raster_array.shape
    raster_prj = raster_ds.GetProjection()
    raster_geotrans = raster_ds.GetGeoTransform()
    raster_upleft_x, raster_x_size, _, raster_upleft_y, _, raster_y_size = raster_geotrans

    # Compute coords using geotransform, adding half a cell to get middle of pixel
    x_coords = [x * float(raster_x_size) + raster_upleft_x + (float(raster_x_size) / 2) for x in x_inds]
    y_coords = [y * float(raster_y_size) + raster_upleft_y + (float(raster_y_size) / 2) for y in y_inds]
    
    # Return coords
    return x_coords, y_coords


def coords_to_indices(x_coords, y_coords, input_raster, strip_outofrange=False):
    
    """
    Takes lists of x and y coordinates and converts to equivelent raster array cell indices.
    For example, an x-y coordinate located within the very top-left cell of a raster's array will have
    indices (0, 0). This function is the inverse of indices_to_coords.
    
    A potential use of this function is to identify raster cells that fall beneath a set of x-y coordinate 
    points; the resulting x and y indices can then be used to extract data from the input raster 
    (i.e. raster_array[y_inds, x_inds]):
    
    >>> raster_path = "test.tif"    
    >>> raster_ds = gdal.Open(raster_path)
    >>> raster_array = raster_ds.GetRasterBand(1).ReadAsArray()
    >>> x_inds, y_inds = coords_to_indices(x_coords=[152.2, 155.3], 
    >>>                                    y_coords=[-17.5, -16.3], input_raster=raster_path)  
    >>> raster_array[y_inds, x_inds]
    
    Last modified: April 2018
    Author: Robbi Bishop-Taylor
    
    :param x_coords: 
        List of x coordinates (or longitudes) in the same projection system
        as input_raster
        
    :param y_coords: 
        List of y coordinates (or latitudes) in the same projection system as input_raster
        
    :param input_raster: 
        Path to raster used to convert x and y coordinates into indices of raster cells
        
    :param strip_outofrange: 
        If coordinates occur outside of the bounds of a raster, the resulting indices will not exist 
        within the raster and attempting to use these  indices to extract data from the raster's array 
        (i.e. raster_array[y_inds, x_inds]) will fail. To prevent this, set strip_outofrange=True to 
        drop all indices that occur outside the input raster
                            
    :return x_inds: 
        List of x indices of raster cells for each input x coordinate 
        
    :return y_inds: 
        List of y indices of raster cells for each input y coordinate 
    """
    
    # Import raster
    raster_ds = gdal.Open(input_raster)
    raster_array = raster_ds.GetRasterBand(1).ReadAsArray() 
    raster_rows, raster_cols = raster_array.shape
    raster_prj = raster_ds.GetProjection()
    raster_geotrans = raster_ds.GetGeoTransform()
    raster_upleft_x, raster_x_size, _, raster_upleft_y, _, raster_y_size = raster_geotrans

    # Compute indices using geotransform
    x_inds = [int((x_coord - raster_upleft_x) / float(raster_x_size)) for x_coord in x_coords] 
    y_inds = [int((y_coord - raster_upleft_y) / float(raster_y_size)) for y_coord in y_coords] 
    
    # Optionally remove all indices that fall outside the bounds of the input raster    
    if strip_outofrange:
        
        within_range = [(x, y) for (x, y) in zip(x_inds, y_inds) if 
                        (x >= 0 and y >= 0 and x < raster_cols and y < raster_rows)] 
        x_inds, y_inds = zip(*within_range)
    
    # Return indices
    return x_inds, y_inds


def raster_randomsample(n_samples, input_raster, nodata=None, prob=False, replace=True): 
    
    """
    Generate a set of n random points within cells of a raster that contain data. Can optionally
    use raster values to define probability of a random point being placed within a raster cell
    (e.g. for stratified random sampling).
    
    Last modified: April 2018
    Author: Robbi Bishop-Taylor

    :param n_samples: 
        Number of points to generate
        
    :param input_raster: 
        Path of raster used to generate points
        
    :param nodata: 
        Optional nodata value if raster does not have nodata set automatically
        
    :param prob: 
        If prob=True, generate samples using probabilities calculated from raster 
        values; raster values are rescaled to sum to 1.0 with high values having a 
        greater chance of producing random points
        
    :param replace: 
        If replace=False, only generate one sample per input raster cell. 
        Alternatively, replace=True allows multiple samples to be randomly 
        generated within individual raster cells

    :return: 
        Lists of x coordinates and y coordinates in coordinate system of input_raster        
    """   

    # Read in data 
    raster_ds = gdal.Open(input_raster)
    raster_band = raster_ds.GetRasterBand(1)
    raster_array = raster_band.ReadAsArray() 

    # Identify indexes of pixels containing data
    data_inds_y, data_inds_x = np.nonzero((raster_array != nodata) & 
                                          (raster_array != raster_band.GetNoDataValue()))

    # Create set of random indices to use to index into list of pixels containing data; if prob = True,
    # compute random samples using raster values re-scaled to sum to 1
    if prob:

        # Compute scaled values for prop sampling
        values = raster_array[data_inds_y, data_inds_x]
        values_rescaled = (values - values.min()) / (values.max() - values.min())
        probs = values_rescaled / values_rescaled.sum()

        # Randomly select index values using probabilities from raster values
        ix = np.random.choice(len(data_inds_y), n_samples, p=probs, replace=replace)

    else:

        # Randomly select index values
        ix = np.random.choice(len(data_inds_y), n_samples, replace=replace)

    # Add one pixel of random variation so random points can occur at any location within a raster pixel
    sample_inds_x = data_inds_x[ix] + np.random.uniform(-0.5, 0.5, n_samples)
    sample_inds_y = data_inds_y[ix] + np.random.uniform(-0.5, 0.5, n_samples)

    # Convert into spatial coordinates
    x_coords, y_coords = indices_to_coords(x_inds=sample_inds_x,
                                           y_inds=sample_inds_y,
                                           input_raster=input_raster)
    
    # Return lists of output x and y spatial coordinates
    return x_coords, y_coords


def array_to_geotiff(fname, data, geo_transform, projection,
                     nodata_val=0, dtype=gdal.GDT_Float32):
    """
    Create a single band GeoTIFF file with data from an array. 
    
    Because this works with simple arrays rather than xarray datasets from DEA, it requires
    geotransform info ("(upleft_x, x_size, x_rotation, upleft_y, y_rotation, y_size)") and 
    projection data (in "WKT" format) for the output raster. These are typically obtained from 
    an existing raster using the following GDAL calls:
    
    >>>  import gdal
    >>>  gdal_dataset = gdal.Open(raster_path)
    >>>  geotrans = gdal_dataset.GetGeoTransform()
    >>>  prj = gdal_dataset.GetProjection()
    
    ...or alternatively, directly from an xarray dataset:
    
    >>>  geotrans = xarraydataset.geobox.transform.to_gdal()
    >>>  prj = xarraydataset.geobox.crs.wkt
    
    Last modified: March 2018
    Author: Robbi Bishop-Taylor
    
    :param fname: 
        Output geotiff file path including extension
        
    :param data: 
        Input array to export as a geotiff
        
    :param geo_transform: 
        Geotransform for output raster; e.g. "(upleft_x, x_size, x_rotation, 
        upleft_y, y_rotation, y_size)"
        
    :param projection:
        Projection for output raster (in "WKT" format)
        
    :param nodata_val: 
        Value to convert to nodata in the output raster; default 0
        
    :param dtype: 
        Optionally set the dtype of the output raster; can be useful when exporting 
        an array of float or integer values. Defaults to gdal.GDT_Float32
        
    """

    # Set up driver
    driver = gdal.GetDriverByName('GTiff')

    # Create raster of given size and projection
    rows, cols = data.shape
    dataset = driver.Create(fname, cols, rows, 1, dtype)
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)

    # Write data to array and set nodata values
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)
    band.SetNoDataValue(nodata_val)

    # Close file
    dataset = None
    
    
def reproject_to_template(input_raster, template_raster, output_raster, resolution=None,
                         resampling=gdal.GRA_Bilinear, nodata_val=0):
    
    """
    Reprojects a raster to match the extent, cell size, projection and dimensions of a template 
    raster using GDAL. Optionally, can set custom resolution for output reprojected raster using 
    'resolution'; this will affect raster dimensions/width/columns.
    
    Last modified: April 2018
    Author: Robbi Bishop-Taylor    
    
    :param input_raster: 
        Path to input geotiff raster to be reprojected (.tif)
        
    :param template_raster: 
        Path to template geotiff raster (.tif) used to copy extent, projection etc
        
    :param output_raster: 
        Output reprojected raster path with geotiff extension (.tif)
        
    :param resolution: 
        Optionally set custom cell size for output reprojected raster; defaults to 
        'None', or the cell size of template raster 
        
    :param resampling: 
        GDAL resampling method to use for reprojection; defaults to gdal.GRA_Bilinear 
        
    :param nodata_val: 
        Values in the output reprojected raster to set to nodata; defaults to 0
    
    :return: 
        GDAL dataset for further analysis, and raster written to output_raster (if this
        dataset appears empty when loaded into a GIS, close the dataset like 'output_ds = None')
        
    """
    
    # Import raster to reproject
    print("Importing raster datasets")
    input_ds = gdal.Open(input_raster)
    input_proj = input_ds.GetProjection()
    input_geotrans = input_ds.GetGeoTransform()
    data_type = input_ds.GetRasterBand(1).DataType
    n_bands = input_ds.RasterCount  
    
    # Import raster to use as template
    template_ds = gdal.Open(template_raster)   
    template_proj = template_ds.GetProjection()
    template_geotrans = template_ds.GetGeoTransform()
    template_w = template_ds.RasterXSize
    template_h = template_ds.RasterYSize
    
    # Use custom resolution if supplied
    if resolution:
        
        template_geotrans[1] = float(resolution)
        template_geotrans[-1] = -float(resolution)

    # Create new output dataset to reproject into
    output_ds = gdal.GetDriverByName('Gtiff').Create(output_raster, template_w, 
                                                     template_h, n_bands, data_type)  
    output_ds.SetGeoTransform(template_geotrans)
    output_ds.SetProjection(template_proj)
    output_ds.GetRasterBand(1).SetNoDataValue(nodata_val)

    # Reproject raster into output dataset
    print("Reprojecting raster")
    gdal.ReprojectImage(input_ds, output_ds, input_proj, template_proj, resampling)
    
    # Close datasets
    input_ds = None
    template_ds = None    
    
    print("Reprojected raster exported to {}".format(output_raster))
    return output_ds
