# SpatialTools.py
"""
This file contains a set of python functions for manipulating rasters and shapefiles that do not 
specifically rely on DEA functionality (i.e. no dc.load or xarrays)

Available functions:

    rasterize_vector
    contour_extract
    indices_to_coords
    coords_to_indices
    raster_randomsample
    array_to_geotiff
    reproject_to_template

Last modified: September 2018
Author: Robbi Bishop-Taylor

"""

import gdal
import affine
import fiona
import collections
import numpy as np
from skimage.measure import find_contours
from shapely.geometry import MultiLineString, mapping


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
    
        import gdal
        gdal_dataset = gdal.Open(raster_path)
        out_array = gdal_dataset.GetRasterBand(1).ReadAsArray()
        geo_transform = gdal_dataset.GetGeoTransform()
        projection = gdal_dataset.GetProjection()
        cols, rows = out_array.shape
    
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


def contour_extract(z_values, ds_array, ds_crs, ds_affine, output_shp=None, min_vertices=2,
                    attribute_data=None, attribute_dtypes=None):

    """
    Uses `skimage.measure.find_contours` to extract contour lines from a two-dimensional array.
    Contours are extracted as a dictionary of xy point arrays for each contour z-value, and optionally as
    line shapefile with one feature per contour z-value.

    The `attribute_data` and `attribute_dtypes` parameters can be used to pass custom attributes to the output
    shapefile.

    Last modified: September 2018
    Author: Robbi Bishop-Taylor

    :param z_values:
        A list of numeric contour values to extract from the array.

    :param ds_array:
        A two-dimensional array from which contours are extracted. This can be a numpy array or xarray DataArray.
        If an xarray DataArray is used, ensure that the array has one two dimensions (e.g. remove the time dimension
        using either `.isel(time=0)` or `.squeeze('time')`).

    :param ds_crs:
        Either a EPSG string giving the coordinate system of the array (e.g. 'EPSG:3577'), or a crs
        object (e.g. from an xarray dataset: `xarray_ds.geobox.crs`).

    :param ds_affine:
        Either an affine object from a rasterio or xarray object (e.g. `xarray_ds.geobox.affine`), or a gdal-derived
        geotransform object (e.g. `gdal_ds.GetGeoTransform()`) which will be converted to an affine.

    :param min_vertices:
        An optional integer giving the minimum number of vertices required for a contour to be extracted. The default
        (and minimum) value is 2, which is the smallest number required to produce a contour line (i.e. a start and
        end point). Higher values remove smaller contours, potentially removing noise from the output dataset.

    :param output_shp:
        An optional string giving a path and filename for the output shapefile. Defaults to None, which
        does not generate a shapefile.

    :param attribute_data:
        An optional dictionary of lists used to define attributes/fields to add to the shapefile. Dict keys give
        the name of the shapefile attribute field, while dict values must be lists of the same length as `z_values`.
        For example, if `z_values=[0, 10, 20]`, then `attribute_data={'type: [1, 2, 3]}` can be used to create a
        shapefile field called 'type' with a value for each contour in the shapefile. The default is None, which
        produces a default shapefile field called 'z_value' with values taken directly from the `z_values` parameter
        and formatted as a 'float:9.2'.

    :param attribute_dtypes:
        An optional dictionary giving the output dtype for each shapefile attribute field that is specified by
        `attribute_data`. For example, `attribute_dtypes={'type: 'int'}` can be used to set the 'type' field to an
        integer dtype. The dictionary should have the same keys/field names as declared in `attribute_data`.
        Valid values include 'int', 'str', 'datetime, and 'float:X.Y', where X is the minimum number of characters
        before the decimal place, and Y is the number of characters after the decimal place.

    :return:
        A dictionary with contour z-values as the dict key, and a list of xy point arrays as dict values.

    :example:

    >>> # Import modules
    >>> import sys
    >>> import datacube

    >>> # Import external dea-notebooks functions using relative link to Scripts directory
    >>> sys.path.append('../10_Scripts')
    >>> import SpatialTools

    >>> # Set up datacube instance
    >>> dc = datacube.Datacube(app='Contour extraction')

    >>> # Define an elevation query
    >>> elevation_query = {'lat': (-35.25, -35.35),
    ...                    'lon': (149.05, 149.17),
    ...                    'output_crs': 'EPSG:3577',
    ...                    'resolution': (-25, 25)}

    >>> # Import sample elevation data
    >>> elevation_data = dc.load(product='srtm_dem1sv1_0', **elevation_query)

    >>> # Remove the time dimension so that array is two-dimensional
    >>> elevation_2d = elevation_data.dem_h.squeeze('time')

    >>> # Extract contours
    >>> contour_dict = SpatialTools.contour_extract(z_values=[600, 700, 800],
    ...                                             ds_array=elevation_2d,
    ...                                             ds_crs=elevation_2d.geobox.crs,
    ...                                             ds_affine=elevation_2d.geobox.affine,
    ...                                             output_shp='extracted_contours.shp')
    Extracting contour 600
    Extracting contour 700
    Extracting contour 800
    <BLANKLINE>
    Exporting contour shapefile to extracted_contours.shp

    """

    # First test that input array has only two dimensions:
    if len(ds_array.shape) == 2:

        # Obtain affine object from either rasterio/xarray affine or a gdal geotransform:
        if type(ds_affine) != affine.Affine:

            ds_affine = affine.Affine.from_gdal(*ds_affine)

        ####################
        # Extract contours #
        ####################

        # Output dict to hold contours for each offset
        contours_dict = collections.OrderedDict()

        for z_value in z_values:

            # Extract contours and convert output array pixel coordinates into arrays of real world Albers coordinates.
            # We need to add (0.5 x the pixel size) to x values and subtract (-0.5 * pixel size) from y values to
            # correct coordinates to give the centre point of pixels, rather than the top-left corner
            print(f'Extracting contour {z_value}')
            ps = ds_affine[0]  # Compute pixel size
            contours_geo = [np.column_stack(ds_affine * (i[:, 1], i[:, 0])) + np.array([0.5 * ps, -0.5 * ps]) for i in
                            find_contours(ds_array, z_value)]

            # For each array of coordinates, drop any xy points that have NA
            contours_nona = [i[~np.isnan(i).any(axis=1)] for i in contours_geo]

            # Drop 0 length and add list of contour arrays to dict
            contours_withdata = [i for i in contours_nona if len(i) >= min_vertices]

            # If there is data for the contour, add to dict:
            if len(contours_withdata) > 0:
                contours_dict[z_value] = contours_withdata
            else:
                print(f'    No data for contour {z_value}; skipping')

        #######################
        # Export to shapefile #
        #######################

        # If a shapefile path is given, generate shapefile
        if output_shp:

            print(f'\nExporting contour shapefile to {output_shp}')

            # If attribute fields are left empty, default to including a single z-value field based on `z_values`
            if not attribute_data:

                # Default field uses two decimal points by default
                attribute_data = {'z_value': z_values}
                attribute_dtypes = {'z_value': 'float:9.2'}

            # Set up output multiline shapefile properties
            schema = {'geometry': 'MultiLineString',
                      'properties': attribute_dtypes}

            # Create output shapefile for writing
            with fiona.open(output_shp, 'w',
                            crs={'init': str(ds_crs), 'no_defs': True},
                            driver='ESRI Shapefile',
                            schema=schema) as output:

                # Write each shapefile to the dataset one by one
                for i, (z_value, contours) in enumerate(contours_dict.items()):

                    # Create multi-string object from all contour coordinates
                    contour_multilinestring = MultiLineString(contours)

                    # Get attribute values for writing
                    attribute_vals = {field_name: field_vals[i] for field_name, field_vals in attribute_data.items()}

                    # Write output shapefile to file with z-value field
                    output.write({'properties': attribute_vals,
                                  'geometry': mapping(contour_multilinestring)})

        # Return dict of contour arrays
        return contours_dict

    else:
        print(f'The input `ds_array` has shape {ds_array.shape}. Please input a two-dimensional array (if your '
              f'input array has a time dimension, remove it using `.isel(time=0)` or `.squeeze(\'time\')`)')


def indices_to_coords(x_inds, y_inds, input_raster):
    
    """
    Takes lists of x and y array indices and converts them to corresponding spatial x and y 
    coordinates. For example, the very top-left cell of a raster's array will have indices (0, 0), but 
    when converted to spatial coordinates this cell location may be equivelent to a point with XXX.00 
    longitude, -XX.00 latitude. 
    
    This function can be used to identify the real-world spatial coordinates of raster cells meeting 
    certain criteria, i.e.:
    
        raster_path = "test.tif"
        raster_ds = gdal.Open(raster_path)
        raster_array = raster_ds.GetRasterBand(1).ReadAsArray()
        y_inds, x_inds = np.nonzero(raster_array > 50)  # this computes indices of cells that are not 0
        indices_to_coords(x_inds=x_inds, x_inds=y_inds, input_raster=raster_path)
    
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
    
        raster_path = "test.tif"
        raster_ds = gdal.Open(raster_path)
        raster_array = raster_ds.GetRasterBand(1).ReadAsArray()
        x_inds, y_inds = coords_to_indices(x_coords=[152.2, 155.3],
                                           y_coords=[-17.5, -16.3], input_raster=raster_path)
        raster_array[y_inds, x_inds]
    
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
    
        import gdal
        gdal_dataset = gdal.Open(raster_path)
        geotrans = gdal_dataset.GetGeoTransform()
        prj = gdal_dataset.GetProjection()
    
    ...or alternatively, directly from an xarray dataset:
    
        geotrans = xarraydataset.geobox.transform.to_gdal()
        prj = xarraydataset.geobox.crs.wkt
    
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


# The following tests are run if the module is called directly (not when being imported).
# To do this, run the following: `python {modulename}.py`

if __name__ == '__main__':
    # Import doctest to test our module for documentation
    import doctest

    # Run all reproducible examples in the module and test against expected outputs
    print('Testing...')
    doctest.testmod(optionflags=doctest.ELLIPSIS)
    print('Testing complete')
