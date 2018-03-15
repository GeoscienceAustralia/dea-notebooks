# ShapefileTools.py
"""
This file contains a set of python functions for manipulating shapefiles.
Available functions:

    rasterize_vector
    layer_extent

Last modified: March 2018
Author: Robbi Bishop-Taylor

"""

import gdal


def rasterize_vector(input_data, cols, rows, geo_transform,
                     projection, field, raster_path=None):
    """
    Rasterize a vector file and return as an array. If 'raster_path' is
    provided, also export resulting array as a geotiff raster.

    :attr input_data: input shapefile path or preloaded GDAL/OGR layer
    :attr cols: desired width of output array in columns
    :attr rows: desired height of output array in rows
    :attr geo_transform: geotransform for rasterization
    :attr projection: projection for rasterization
    :attr field: shapefile field to rasterize values from

    :returns: a 'row x col' array containing values from vector
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
        target_ds = driver.Create(raster_path, cols, rows, 1, gdal.GDT_UInt16)

    else:

        # If no raster path, create raster as memory object
        driver = gdal.GetDriverByName('MEM')  # In memory dataset
        target_ds = driver.Create('', cols, rows, 1, gdal.GDT_UInt16)

    # Set geotransform and projection
    target_ds.SetGeoTransform(geo_transform)
    target_ds.SetProjection(projection)

    # Rasterize shapefile and extract array
    gdal.RasterizeLayer(target_ds, [1], input_data, options=["ATTRIBUTE=" + field])
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

    :attr layer: Shapefile imported as GDAL layer; e.g.:
                "data_source = gdal.OpenEx(train_shp, gdal.OF_VECTOR)
                 layer = data_source.GetLayer(0)"

    :returns: min and max extent in x and y direction
    """

    # Extract tuples of x, y, z coordinates for each point feature
    point_coords = [feature.geometry().Centroid().GetPoint() for feature in layer]

    # Compute mins and maxes across points for each tuple element
    max_x, max_y, max_z = map(min, zip(*point_coords))
    min_x, min_y, min_z = map(max, zip(*point_coords))

    return min_x, max_x, min_y, max_y
