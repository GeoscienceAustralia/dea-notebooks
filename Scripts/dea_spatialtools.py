## dea_spatialtools.py
'''
Description: This file contains a set of python functions for conducting spatial analyses on Digital Earth Australia data.

License: The code in this notebook is licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth Australia data is licensed under the Creative Commons by Attribution 4.0 license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: September 2019

'''

# Import required packages
import fiona
import affine
import collections
import numpy as np
import geopandas as gpd
from skimage.measure import find_contours
from shapely.geometry import MultiLineString, mapping


def contour_extract(ds_array,
                    z_values,
                    ds_crs,
                    ds_affine,
                    output_shp,
                    min_vertices=2,
                    attribute_data=None,
                    attribute_dtypes=None,
                    dim='time',
                    verbose=True):
    """
    Uses `skimage.measure.find_contours` to extract multiple z-value 
    contour lines from a two-dimensional array (e.g. multiple elevations
    from a single DEM), or one z-value for each array along a specified 
    dimension of a multi-dimensional array (e.g. to map waterlines 
    across time by extracting a 0 NDVI contour from each individual 
    timestep in an xarray timeseries).    
    
    Contours are exported to file as a shapefile and returned as a 
    geopandas geodataframe with one row per z-value or one row per 
    array along a specified dimension. The `attribute_data` and 
    `attribute_dtypes` parameters can be used to pass custom attributes 
    to the output contour features.
    
    Last modified: October 2019
    
    Parameters
    ----------  
    ds_array : xarray DataArray
        A two-dimensional or multi-dimensional array from which 
        contours are extracted. If a two-dimensional array is provided, 
        the analysis will run in 'single array, multiple z-values' mode 
        which allows you to specify multiple `z_values` to be extracted.
        If a multi-dimensional array is provided, the analysis will run 
        in 'single z-value, multiple arrays' mode allowing you to 
        extract contours for each array along the dimension specified 
        by the `dim` parameter.  
    z_values : int, float or list of ints, floats
        An individual z-value or list of multiple z-values to extract 
        from the array. If operating in 'single z-value, multiple 
        arrays' mode specify only a single z-value.
    ds_crs : string or CRS object
        Either a EPSG string giving the coordinate system of the array 
        (e.g. 'EPSG:3577'), or a crs object (e.g. from an xarray 
        dataset: `xarray_ds.geobox.crs`).
    ds_affine : affine.Affine object or GDAL geotransform
        Either an affine object from a rasterio or xarray object 
        (e.g. `xarray_ds.geobox.affine`), or a gdal-derived  
        geotransform object (e.g. `gdal_ds.GetGeoTransform()`) which 
        will be converted to an affine.
    output_shp : string
        The path and filename for the output shapefile.
    min_vertices : int, optional
        The minimum number of vertices required for a contour to be 
        extracted. The default (and minimum) value is 2, which is the 
        smallest number required to produce a contour line (i.e. a start
        and end point). Higher values remove smaller contours, 
        potentially removing noise from the output dataset.
    attribute_data : dict of lists, optional
        An optional dictionary of lists used to define custom 
        attributes/fields to add to the shapefile. Dict keys give the 
        name of the shapefile field, while dict values must be lists of 
        the same length as `z_values` (for 'single array, multiple 
        z-values' mode) or the number of arrays along the dimension 
        specified by the `dim` parameter (for 'single z-value, multiple 
        arrays' mode). For example, if `z_values=[0, 10, 20]`, then 
        `attribute_data={'type: [1, 2, 3]}` can be used to create a 
        shapefile field called 'type' with a value for each contour in 
        the shapefile. The default is None, which produces a default 
        shapefile field called 'z_value' with values taken directly from
        the `z_values` parameter and formatted as a 'float:9.2' ('single
        array, multiple z-values' mode), or a field named after `dim` 
        numbered from 0 to the total number of arrays along the `dim` 
        dimension ('single z-value, multiple arrays' mode).
    attribute_dtypes : dict, optional
        An optional dictionary giving the output dtype for each custom 
        shapefile attribute field specified by `attribute_data`. For 
        example, `attribute_dtypes={'type: 'int'}` can be used to set 
        the 'type' field to an integer dtype. The dictionary should have
        the same keys/field names as declared in `attribute_data`. Valid
        values include 'int', 'str', 'datetime, and 'float:X.Y', where X
        is the minimum number of characters before the decimal place, 
        and Y is the number of characters after the decimal place.
    dim : string, optional
        The name of the dimension along which to extract contours when 
        operating in 'single z-value, multiple arrays' mode. The default
        is 'time', which extracts contours for each array along the time
        dimension.
    verbose: bool, optional
        Whether to print the result of each contour extraction to the 
        console. The default is True which prints all results; set to 
        False for a cleaner output, particularly when extracting large 
        numbers of contours.
    Returns
    -------
    output_gdf : geopandas geodataframe
        A geopandas geodataframe object with one feature per z-value 
        ('single array, multiple z-values' mode), or one row per array 
        along the dimension specified by the `dim` parameter ('single 
        z-value, multiple arrays' mode). If `attribute_data` and 
        `attribute_dtypes` are provided, these values will be included 
        in the shapefile's attribute table.
        
    """

    # Obtain affine object from either rasterio/xarray affine or a 
    # gdal geotransform:
    if type(ds_affine) != affine.Affine:
        ds_affine = affine.Affine.from_gdal(*ds_affine)

    # If z_values is supplied is not a list, convert to list:
    z_values = z_values if isinstance(z_values, list) else [z_values]

    # If array has only one layer along the `dim` dimension (e.g. time), 
    # remove the dim:
    try:
        ds_array = ds_array.squeeze(dim=dim)
        print(f"Dimension '{dim}' has length of 1; removing from array")

    except:
        pass

    ########################################
    # Single array, multiple z-values mode #
    ########################################

    # Output dict to hold contours for each offset
    contours_dict = collections.OrderedDict()

    # If array has only two dimensions, run in single array, 
    # multiple z-values mode:
    if len(ds_array.shape) == 2:

        if verbose: print(f'Operating in single array, multiple z-values mode')

        # If no custom attributes given, default to including a single 
        # z-value field based on `z_values`
        if not attribute_data:

            # Default field uses two decimal points by default
            attribute_data = {'z_value': z_values}
            attribute_dtypes = {'z_value': 'float:9.2'}

        # If custom attributes are provided, test that they are equal 
        # in length to the number of `z-values`:
        else:

            for key, values in attribute_data.items():

                if len(values) != len(z_values):

                    raise Exception(
                        f"Supplied attribute '{key}' has length of {len(values)} while z_values has "
                        f"length of {len(z_values)}; please supply the same number of attribute values "
                        "as z_values")

        for z_value in z_values:

            # Extract contours and convert output array cell coords 
            # into arrays of coordinate reference system coords.
            # We need to add (0.5 x the pixel size) to the x and y 
            # values to correct coordinates to give the centre
            # point of pixels, rather than the top-left corner
            if verbose: print(f'    Extracting contour {z_value}')
            ps_x = ds_affine[0]  # Compute pixel x size
            ps_y = ds_affine[4]  # Compute pixel y size
            contours_geo = [
                np.column_stack(ds_affine * (i[:, 1], i[:, 0])) +
                np.array([0.5 * ps_x, 0.5 * ps_y])
                for i in find_contours(ds_array, z_value)
            ]

            # For each array of coordinates, drop xy points that have NA
            contours_nona = [i[~np.isnan(i).any(axis=1)] for i in contours_geo]

            # Drop 0 length and add list of contour arrays to dict
            contours_withdata = [i for i in contours_nona 
                                 if len(i) >= min_vertices]

            # If there is data for the contour, add to dict:
            if len(contours_withdata) > 0:
                contours_dict[z_value] = contours_withdata

            else:
                if verbose:
                    print(f'    No data for contour {z_value}; skipping')
                contours_dict[z_value] = None

                
    ########################################
    # Single z-value, multiple arrays mode #
    ########################################

    # For inputs with more than two dimensions, run in single z-value, 
    # multiple arrays mode:
    else:

        # Test if only a single z-value is given when operating in 
        # single z-value, multiple arrays mode
        print(f'Operating in single z-value, multiple arrays mode')
        if len(z_values) > 1:
            raise Exception('Please provide a single z-value when operating '
                            'in single z-value, multiple arrays mode')

        # If no custom attributes given, default to including one field 
        # based on the `dim` dimension:
        if not attribute_data:

            # Default field is numbered from 0 to the number of arrays 
            # along the `dim` dimension:
            attribute_data = {dim: range(0, len(ds_array[dim]))}
            attribute_dtypes = {dim: 'int'}

        # If custom attributes are provided, test that they are equal 
        # in length to the number of arrays along `dim`:
        else:

            for key, values in attribute_data.items():

                if len(values) != len(ds_array[dim]):

                    raise Exception(
                        f"Supplied attribute '{key}' has length of {len(values)} while there are "
                        f"{len(ds_array[dim])} arrays along the '{dim}' dimension. Please supply "
                        f"the same number of attribute values as arrays along the '{dim}' dimension"
                    )

        for z_value, _ in enumerate(ds_array[dim]):

            # Extract contours and convert output array cell coords into 
            # arrays of coordinate reference system coords. We need to 
            # add (0.5 x the pixel size) to the x and y values to 
            # correct coordinates to give the centre point of pixels, 
            # rather than the top-left corner
            if verbose: print(f'    Extracting contour {z_value}')
            ps_x = ds_affine[0]  # Compute pixel x size
            ps_y = ds_affine[4]  # Compute pixel y size
            contours_geo = [
                np.column_stack(ds_affine * (i[:, 1], i[:, 0])) +
                np.array([0.5 * ps_x, 0.5 * ps_y]) for i in find_contours(
                    ds_array.isel({dim: z_value}), z_values[0])
            ]

            # For each array of coordinates, drop any xy points that have NA
            contours_nona = [i[~np.isnan(i).any(axis=1)] for i in contours_geo]

            # Drop 0 length and add list of contour arrays to dict
            contours_withdata = [
                i for i in contours_nona if len(i) >= min_vertices
            ]

            # If there is data for the contour, add to dict:
            if len(contours_withdata) > 0:
                contours_dict[z_value] = contours_withdata

            else:
                if verbose:
                    print(f'    No data for contour {z_value}; skipping')
                contours_dict[z_value] = None

    #######################
    # Export to shapefile #
    #######################

    # If a shapefile path is given, generate shapefile
    if output_shp:

        if verbose: print(f'Exporting contour shapefile to {output_shp}')

        # Set up output multiline shapefile properties
        schema = {'geometry': 'MultiLineString', 
                  'properties': attribute_dtypes}

        # Create output shapefile for writing
        with fiona.open(output_shp,
                        'w',
                        crs={
                            'init': str(ds_crs),
                            'no_defs': True
                        },
                        driver='ESRI Shapefile',
                        schema=schema) as output:

            # Write each shapefile to the dataset one by one
            for i, (z_value, contours) in enumerate(contours_dict.items()):

                if contours:

                    # Create multi-string object from all contour coordinates
                    contour_multilinestring = MultiLineString(contours)

                    # Get attribute values for writing
                    attribute_vals = {field_name: field_vals[i] 
                                      for field_name, field_vals 
                                      in attribute_data.items()}

                    # Write output shapefile to file with z-value field
                    output.write({
                        'properties': attribute_vals,
                        'geometry': mapping(contour_multilinestring)
                    })

    # Return dict of contour arrays
    output_gdf = gpd.read_file(output_shp)
    return output_gdf




