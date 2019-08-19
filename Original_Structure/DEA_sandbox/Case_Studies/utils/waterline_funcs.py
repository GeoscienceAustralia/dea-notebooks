# waterline_extraction.py
"""

Additional functions for waterline extraction notebook

Last modified: March 2019
Author: Robbi Bishop-Taylor

"""

import xarray as xr
import affine
import fiona
import collections
import numpy as np
import geopandas as gpd
import scipy.interpolate
from scipy import ndimage as nd
from datacube.storage import masking
from skimage.measure import find_contours
from shapely.geometry import MultiLineString, mapping
import matplotlib as mpl
import matplotlib.cm
import matplotlib.colors
from ipyleaflet import Map, Marker, Popup, GeoJSON, basemaps


def load_cloudmaskedlandsat(dc, query, platforms=['ls5t', 'ls7e', 'ls8c'], 
                            bands=['nbart_red', 'nbart_green', 'nbart_blue', 
                                   'nbart_nir', 'nbart_swir_1', 'nbart_swir_2'],
                            rename_bands=True):
    
    '''
    This function returns cloud-masked Landsat Collection 3 `ga_{platform}_ard_3` 
    data by loading both Landsat and masking out any pixels affected by cloud, cloud shadow, 
    or any pixels missing data in any band. For convenience, the resulting data is returned 
    with sensible band names (e.g. 'red', 'green', 'blue') instead of the unnamed bands in the
    original data.
    
    Last modified: July 2019
    Author: Robbi Bishop-Taylor
    
    Parameters
    ----------  
    dc : datacube Datacube object
        A specific Datacube to import from, i.e. `dc = datacube.Datacube(app='Clear Landsat')`. 
        This allows you to also use development datacubes if required.    
    query : dict
        A dict containing the query bounds. Can include lat/lon, time etc. If no `time` query is 
        given, the function defaults to all timesteps available to all sensors (e.g. 1987-2018)
    platforms : list, optional
        An optional Landsat platform name to load data from. Options are 'ls5t', 'ls7e', 'ls8c'.
    bands : list, optional
        An optional list of strings containing the bands to be read in; options default to 
        'nbart_red', 'nbart_green', 'nbart_blue', 'nbart_nir', 'nbart_swir_1', 'nbart_swir_2'.
    rename_bands : bool, optional
        An optiona boolean specifying whether to rename complex 'nbart_swir_2'-style names to
        simpler 'swir2' aliases. This can be used to provide compatability with the previous
        Collection 2 band name aliases. Defaults to True.
        
    Returns
    -------
    landsat_ds : xarray Dataset
        An xarray dataset containing pixel-quality masked Landsat observations        
        
    '''

    # If bands do not include fmask, add it
    new_bands = set(bands)
    new_bands.add('fmask')
    
    # Dictionary mapping full data names to simpler 'red' alias names
    bands_simplenames = {'nbart_red': 'red',
                         'nbart_green': 'green',
                         'nbart_blue': 'blue',
                         'nbart_nir': 'nir',
                         'nbart_swir_1': 'swir1',
                         'nbart_swir_2': 'swir2',
                         'nbar_red': 'red',
                         'nbar_green': 'green',
                         'nbar_blue': 'blue',
                         'nbar_nir': 'nir',
                         'nbar_swir_1': 'swir1',
                         'nbar_swir_2': 'swir2'}
    
    platform_data = []

    for platform in platforms:

        # Load landsat data
        landsat_ds = dc.load(product=f'ga_{platform}_ard_3', 
                             dask_chunks={'time': 1}, 
                             measurements=new_bands,
                             group_by='solar_day', 
                             **query)

        # Mask out all pixels affected by cloud, cloud shadow, or other invalid data
        valid_data = (landsat_ds.fmask == 1) | (landsat_ds.fmask == 4) | (landsat_ds.fmask == 5)
        landsat_ds = landsat_ds.where(valid_data)

        if rename_bands:

            # Rename bands in dataset to use simple names (e.g. 'red')
            bands_to_rename = {a: b for a, b in bands_simplenames.items() if a in bands}
            landsat_ds = landsat_ds[bands].rename(bands_to_rename)

        platform_data.append(landsat_ds)

    return xr.concat(platform_data, dim='time').sortby('time')
    
     
def contour_extract(ds_array, z_values, ds_crs, ds_affine, output_shp, min_vertices=2,
                    attribute_data=None, attribute_dtypes=None, dim='time', verbose=True):

    """
    Uses `skimage.measure.find_contours` to extract multiple z-value contour lines from a two-dimensional array
    (e.g. multiple elevations from a single DEM), or one z-value for each array along a specified dimension of a 
    multi-dimensional array (e.g. to map waterlines across time by extracting a 0 NDVI contour from each individual 
    timestep in an xarray timeseries).    
    
    Contours are exported to file as a shapefile and returned as a geopandas geodataframe with one row per
    z-value or one row per array along a specified dimension. The `attribute_data` and `attribute_dtypes` parameters 
    can be used to pass custom attributes to the output contour features.

    Last modified: March 2019
    Author: Robbi Bishop-Taylor
    
    Parameters
    ----------  
    ds_array : xarra DataArray
        A two-dimensional or multi-dimensional array from which contours are extracted. If a two-dimensional array
        is provided, the analysis will run in 'single array, multiple z-values' mode which allows you to specify 
        multiple `z_values` to be extracted. If a multi-dimensional array is provided, the analysis will run in 
        'single z-value, multiple arrays' mode allowing you to extract contours for each array along the dimension
        specified by the `dim` parameter.  
    z_values : int, float or list of ints, floats
        An individual z-value or list of multiple z-values to extract from the array. If operating in 'single 
        z-value, multiple arrays' mode specify only a single z-value.
    ds_crs : string or CRS object
        Either a EPSG string giving the coordinate system of the array (e.g. 'EPSG:3577'), or a crs
        object (e.g. from an xarray dataset: `xarray_ds.geobox.crs`).
    ds_affine : affine.Affine object or GDAL geotransform
        Either an affine object from a rasterio or xarray object (e.g. `xarray_ds.geobox.affine`), or a gdal-derived
        geotransform object (e.g. `gdal_ds.GetGeoTransform()`) which will be converted to an affine.
    output_shp : string
        The path and filename for the output shapefile.
    min_vertices : int, optional
        The minimum number of vertices required for a contour to be extracted. The default (and minimum) value is 2,
        which is the smallest number required to produce a contour line (i.e. a start and end point). Higher values
        remove smaller contours, potentially removing noise from the output dataset.
    attribute_data : dict of lists, optional
        An optional dictionary of lists used to define custom attributes/fields to add to the shapefile. Dict keys 
        give the name of the shapefile field, while dict values must be lists of the same length as `z_values`
        (for 'single array, multiple z-values' mode) or the number of arrays along the dimension specified by the `dim`
        parameter (for 'single z-value, multiple arrays' mode). For example, if `z_values=[0, 10, 20]`, then 
        `attribute_data={'type: [1, 2, 3]}` can be used to create a shapefile field called 'type' with a value for
        each contour in the shapefile. The default is None, which produces a default shapefile field called 'z_value'
        with values taken directly from the `z_values` parameter and formatted as a 'float:9.2' ('single array, 
        multiple z-values' mode), or a field named after `dim` numbered from 0 to the total number of arrays along 
        the `dim` dimension ('single z-value, multiple arrays' mode).
    attribute_dtypes : dict, optional
        An optional dictionary giving the output dtype for each custom shapefile attribute field specified by
        `attribute_data`. For example, `attribute_dtypes={'type: 'int'}` can be used to set the 'type' field to an
        integer dtype. The dictionary should have the same keys/field names as declared in `attribute_data`.
        Valid values include 'int', 'str', 'datetime, and 'float:X.Y', where X is the minimum number of characters
        before the decimal place, and Y is the number of characters after the decimal place.
    dim : string, optional
        The name of the dimension along which to extract contours when operating in 'single z-value, multiple arrays'
        mode. The default is 'time', which extracts contours for each array along the time dimension.
    verbose: bool, optional
        Whether to print the result of each contour extraction to the console. The default is True which prints all
        results; set to False for a cleaner output, particularly when extracting large numbers of contours.

    Returns
    -------
    output_gdf : geopandas geodataframe
        A geopandas geodataframe object with one feature per z-value ('single array, multiple z-values' mode), or one
        row per array along the dimension specified by the `dim` parameter ('single z-value, multiple arrays' mode). 
        If `attribute_data` and `ttribute_dtypes` are provided, these values will be included in the shapefile's 
        attribute table.

    Example
    -------   
    >>> # Import modules
    >>> import sys
    >>> import datacube

    >>> # Import external dea-notebooks functions using relative link to Scripts directory
    >>> sys.path.append('../10_Scripts')
    >>> import SpatialTools

    >>> # Set up datacube instance
    >>> dc = datacube.Datacube(app='Contour extraction')

    ########################################
    # Single array, multiple z-values mode #
    ########################################
    
    >>> # Define an elevation query
    >>> elevation_query = {'lat': (-35.25, -35.35),
    ...                    'lon': (149.05, 149.17),
    ...                    'output_crs': 'EPSG:3577',
    ...                    'resolution': (-25, 25)}

    >>> # Import sample elevation data
    >>> elevation_data = dc.load(product='srtm_dem1sv1_0', **elevation_query)

    >>> # Extract contours
    >>> contour_gdf = SpatialTools.contour_extract(z_values=[600, 700, 800],
    ...                                            ds_array=elevation_data.dem_h,
    ...                                            ds_crs=elevation_data.geobox.crs,
    ...                                            ds_affine=elevation_data.geobox.affine,
    ...                                            output_shp='extracted_contours.shp')
    Dimension 'time' has length of 1; removing from array
    Operating in single array, multiple z-values mode
        Extracting contour 600
        Extracting contour 700
        Extracting contour 800
    Exporting contour shapefile to extracted_contours.shp
    
    ########################################
    # Single z-value, multiple arrays mode #
    ########################################
    
    >>> # Define a Landsat query
    >>> landsat_query = {'lat': (-35.25, -35.35),
    ...                  'lon': (149.05, 149.17),
    ...                  'time': ('2016-02-15', '2016-03-01'),
    ...                  'output_crs': 'EPSG:3577',
    ...                  'resolution': (-25, 25)}

    >>> # Import sample Landsat data
    >>> landsat_data = dc.load(product='ls8_nbart_albers', 
    ...                        group_by='solar_day',
    ...                        **landsat_query)
    
    >>> # Test that there are multiple arrays along the 'time' dimension
    >>> print(len(landsat_data.time))
    2

    >>> # Set up custom attributes to be added as shapefile fields
    >>> attribute_data = {'value': ['first_contour', 'second_contour']}
    >>> attribute_dtypes = {'value': 'str'}

    >>> # Extract contours
    >>> contour_gdf = SpatialTools.contour_extract(z_values=3000,
    ...                                            ds_array=landsat_data.red,
    ...                                            ds_crs=landsat_data.geobox.crs,
    ...                                            ds_affine=landsat_data.geobox.affine,
    ...                                            output_shp='extracted_contours.shp',
    ...                                            attribute_data=attribute_data,
    ...                                            attribute_dtypes=attribute_dtypes,
    ...                                            dim='time')
    Operating in single z-value, multiple arrays mode
        Extracting contour 0
        Extracting contour 1
    Exporting contour shapefile to extracted_contours.shp

    """

    # Obtain affine object from either rasterio/xarray affine or a gdal geotransform:
    if type(ds_affine) != affine.Affine:
        ds_affine = affine.Affine.from_gdal(*ds_affine)
        
    # If z_values is supplied is not a list, convert to list before proceeding:      
    z_values = z_values if isinstance(z_values, list) else [z_values]
    
    # If array has only one layer along the `dim` dimension (e.g. time), remove the dim:
    try:
        ds_array = ds_array.squeeze(dim=dim)
        print(f"Dimension '{dim}' has length of 1; removing from array")
        
    except: pass

    
    ########################################
    # Single array, multiple z-values mode #
    ########################################
    
    # Output dict to hold contours for each offset
    contours_dict = collections.OrderedDict()
    
    # If array has only two dimensions, run in single array, multiple z-values mode:
    if len(ds_array.shape) == 2:
        
        print(f'Operating in single array, multiple z-values mode')   
        
        # If no custom attributes given, default to including a single z-value field based on `z_values`
        if not attribute_data:

            # Default field uses two decimal points by default
            attribute_data = {'z_value': z_values}
            attribute_dtypes = {'z_value': 'float:9.2'}
        
        # If custom attributes are provided, test that they are equal in length to the number of `z-values`:
        else:
            
            for key, values in attribute_data.items():
                
                if len(values) != len(z_values): 
                    
                    raise Exception(f"Supplied attribute '{key}' has length of {len(values)} while z_values has "
                                    f"length of {len(z_values)}; please supply the same number of attribute values "
                                    "as z_values")

        for z_value in z_values:

            # Extract contours and convert output array cell coords into arrays of coordinate reference system coords.
            # We need to add (0.5 x the pixel size) to x values and subtract (-0.5 * pixel size) from y values to
            # correct coordinates to give the centre point of pixels, rather than the top-left corner
            if verbose: print(f'    Extracting contour {z_value}')
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
                if verbose: print(f'    No data for contour {z_value}; skipping')
                contours_dict[z_value] = None
            
            
    ########################################
    # Single z-value, multiple arrays mode #
    ########################################
    
    # For inputs with more than two dimensions, run in single z-value, multiple arrays mode:
    else:
        
        # Test if only a single z-value is given when operating in single z-value, multiple arrays mode
        print(f'Operating in single z-value, multiple arrays mode')        
        if len(z_values) > 1: raise Exception('Please provide a single z-value when operating '
                                              'in single z-value, multiple arrays mode')
            
        # If no custom attributes given, default to including one field based on the `dim` dimension:
        if not attribute_data:

            # Default field is numbered from 0 to the number of arrays along the `dim` dimension:
            attribute_data = {dim: range(0, len(ds_array[dim]))}
            attribute_dtypes = {dim: 'int'}
        
        # If custom attributes are provided, test that they are equal in length to the number of arrays along `dim`:
        else:
            
            for key, values in attribute_data.items():
                
                if len(values) != len(ds_array[dim]): 
                    
                    raise Exception(f"Supplied attribute '{key}' has length of {len(values)} while there are "
                                    f"{len(ds_array[dim])} arrays along the '{dim}' dimension. Please supply "
                                    f"the same number of attribute values as arrays along the '{dim}' dimension")
        
        for z_value, _ in enumerate(ds_array[dim]): 

            # Extract contours and convert output array cell coords into arrays of coordinate reference system coords.
            # We need to add (0.5 x the pixel size) to x values and subtract (-0.5 * pixel size) from y values to
            # correct coordinates to give the centre point of pixels, rather than the top-left corner
            if verbose: print(f'    Extracting contour {z_value}')
            ps = ds_affine[0]  # Compute pixel size
            contours_geo = [np.column_stack(ds_affine * (i[:, 1], i[:, 0])) + np.array([0.5 * ps, -0.5 * ps]) for i in
                            find_contours(ds_array.isel({dim: z_value}), z_values[0])]

            # For each array of coordinates, drop any xy points that have NA
            contours_nona = [i[~np.isnan(i).any(axis=1)] for i in contours_geo]

            # Drop 0 length and add list of contour arrays to dict
            contours_withdata = [i for i in contours_nona if len(i) >= min_vertices]

            # If there is data for the contour, add to dict:
            if len(contours_withdata) > 0:
                contours_dict[z_value] = contours_withdata
                
            else:
                if verbose: print(f'    No data for contour {z_value}; skipping')
                contours_dict[z_value] = None
                

    #######################
    # Export to shapefile #
    #######################

    # If a shapefile path is given, generate shapefile
    if output_shp:

        print(f'Exporting contour shapefile to {output_shp}')

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

                if contours:

                    # Create multi-string object from all contour coordinates
                    contour_multilinestring = MultiLineString(contours)

                    # Get attribute values for writing
                    attribute_vals = {field_name: field_vals[i] for field_name, field_vals in 
                                      attribute_data.items()}

                    # Write output shapefile to file with z-value field
                    output.write({'properties': attribute_vals,
                                  'geometry': mapping(contour_multilinestring)})

    # Return dict of contour arrays
    output_gdf = gpd.read_file(output_shp)
    return output_gdf


def rgb(ds, bands=['red', 'green', 'blue'], index=None, index_dim='time', 
        robust=True, percentile_stretch = None, col_wrap=4, size=6, aspect=1,
        savefig_path=None, savefig_kwargs={}, **kwargs):
    
    """
    Takes an xarray dataset and plots RGB images using three imagery bands (e.g true colour ['red', 'green', 'blue']
    or false colour ['swir1', 'nir', 'green']). The `index` parameter allows easily selecting individual or multiple
    images for RGB plotting. Images can be saved to file by specifying an output path using `savefig_path`.
    
    This function was designed to work as an easy-to-use wrapper around xarray's `.plot.imshow()` functionality.
    Last modified: November 2018
    Author: Robbi Bishop-Taylor
    
    Parameters
    ----------  
    ds : xarray Dataset
        A two-dimensional or multi-dimensional array to plot as an RGB image. If the array has more than two 
        dimensions (e.g. multiple observations along a 'time' dimension), either use `index` to select one (`index=0`) 
        or multiple observations (`index=[0, 1]`), or create a custom faceted plot using e.g. `col="time", col_wrap=4`.       
    bands : list of strings, optional
        A list of three strings giving the band names to plot. Defaults to '['red', 'green', 'blue']'.
    index : integer or list of integers, optional
        For convenience `index` can be used to select one (`index=0`) or multiple observations (`index=[0, 1]`) from
        the input dataset for plotting. If multiple images are requested these will be plotted as a faceted plot.
    index_dim : string, optional
        The dimension along which observations should be plotted if multiple observations are requested using `index`.
        Defaults to `time`.
    robust : bool, optional
        Produces an enhanced image where the colormap range is computed with 2nd and 98th percentiles instead of the 
        extreme values. Defaults to True.
    percentile_stretch : tuple of floats
        An tuple of two floats (between 0.00 and 1.00) that can be used to clip the colormap range to manually 
        specified percentiles to get more control over the brightness and contrast of the image. The default is None; 
        '(0.02, 0.98)' is equivelent to `robust=True`. If this parameter is used, `robust` will have no effect.
    col_wrap : integer, optional
        The maximum number of columns allowed in faceted plots. Defaults to 4.
    size : integer, optional
        The height (in inches) of each plot. Defaults to 6.
    aspect : integer, optional
        Aspect ratio of each facet in the plot, so that aspect * size gives width of each facet in inches. Defaults to 1.
    savefig_path : string, optional
        Path to export image file for the RGB plot. Defaults to None, which does not export an image file.
    savefig_kwargs : dict, optional
        A dict of keyword arguments to pass to `matplotlib.pyplot.savefig` when exporting an image file. For options, 
        see: https://matplotlib.org/api/_as_gen/matplotlib.pyplot.savefig.html        
    **kwargs : optional
        Additional keyword arguments to pass to `xarray.plot.imshow()`. For more options, see:
        http://xarray.pydata.org/en/stable/generated/xarray.plot.imshow.html  
    Returns
    -------
    An RGB plot of one or multiple observations, and optionally an image file written to file.
    
    Example
    -------
    >>> # Import modules
    >>> import sys
    >>> import datacube
    >>> # Import external dea-notebooks functions using relative link to Scripts directory
    >>> sys.path.append('../10_Scripts')
    >>> import DEAPlotting
    >>> # Set up datacube instance
    >>> dc = datacube.Datacube(app='RGB plotting')
    >>> # Define a Landsat query
    >>> landsat_query = {'lat': (-35.25, -35.35),
    ...                  'lon': (149.05, 149.17),
    ...                  'time': ('2016-02-15', '2016-03-01'),
    ...                  'output_crs': 'EPSG:3577',
    ...                  'resolution': (-25, 25)}
    >>> # Import sample Landsat data
    >>> landsat_data = dc.load(product='ls8_nbart_albers', 
    ...                        group_by='solar_day',
    ...                        **landsat_query)
    >>> # Plot a single observation (option 1)
    >>> DEAPlotting.rgb(ds=landsat_data.isel(time=0))
    >>> # Plot a single observation using `index` (option 2)
    >>> DEAPlotting.rgb(ds=landsat_data, index=0)
    >>> # Plot multiple observations as a facet plot (option 1)
    >>> DEAPlotting.rgb(ds=landsat_data, col='time')
    >>> # Plot multiple observations as a facet plot using `index` (option 2)
    >>> DEAPlotting.rgb(ds=landsat_data, index=[0, 1])
    >>> # Increase contrast by specifying percentile thresholds using `percentile_stretch`
    >>> DEAPlotting.rgb(ds=landsat_data, index=[0, 1], 
    ...                 percentile_stretch=(0.02, 0.9))
    >>> # Pass in any keyword argument to `xarray.plot.imshow()` (e.g. `aspect`). For more 
    >>> # options, see: http://xarray.pydata.org/en/stable/generated/xarray.plot.imshow.html  
    >>> DEAPlotting.rgb(ds=landsat_data, index=[0, 1], 
    ...                 percentile_stretch=(0.02, 0.9), aspect=1.2)
    >>> # Export the RGB image to file using `savefig_path`
    >>> DEAPlotting.rgb(ds=landsat_data, index=[0, 1], 
    ...                 percentile_stretch=(0.02, 0.9), aspect=1.2, 
    ...                 savefig_path='output_image_test.png')
    Exporting image to output_image_test.png
    
    """   

    # If no value is supplied for `index` (the default), plot using default values and arguments passed via `**kwargs`
    if index is None:
        
        if len(ds.dims) > 2 and 'col' not in kwargs:
            raise Exception(f'The input dataset `ds` has more than two dimensions: {list(ds.dims.keys())}. ' 
                             'Please select a single observation using e.g. `index=0`, or enable faceted '
                             'plotting by adding the arguments e.g. `col="time", col_wrap=4` to the function call')

        # Select bands and convert to DataArray
        da = ds[bands].to_array()
        
        # If percentile_stretch is provided, clip plotting to percentile vmin, vmax
        if percentile_stretch:
            vmin, vmax = da.quantile(percentile_stretch).values
            kwargs.update({'vmin': vmin, 'vmax': vmax})
            
        img = da.plot.imshow(robust=robust, col_wrap=col_wrap, size=size, **kwargs)        
 
    # If values provided for `index`, extract corresponding observations and plot as either single image or facet plot
    else:
        
        # If a float is supplied instead of an integer index, raise exception
        if isinstance(index, float):
            raise Exception(f'Please supply `index` as either an integer or a list of integers')
        
        # If col argument is supplied as well as `index`, raise exception
        if 'col' in kwargs:
            raise Exception(f'Cannot supply both `index` and `col`; please remove one and try again')
            
        # Convert index to generic type list so that number of indices supplied can be computed
        index = index if isinstance(index, list) else [index]
        
        # Select bands and observations and convert to DataArray
        da = ds[bands].isel(**{index_dim: index}).to_array()
        
        # If percentile_stretch is provided, clip plotting to percentile vmin, vmax
        if percentile_stretch:
            vmin, vmax = da.quantile(percentile_stretch).values
            kwargs.update({'vmin': vmin, 'vmax': vmax})
            
        # If multiple index values are supplied, plot as a faceted plot 
        if len(index) > 1:
            
            img = da.plot.imshow(robust=robust, col=index_dim, col_wrap=col_wrap, size=size, **kwargs)
        
        # If only one index is supplied, squeeze out index_dim and plot as a single panel
        else:

            img = da.squeeze(dim=index_dim).plot.imshow(robust=robust, size=size, **kwargs)
    
    # If an export path is provided, save image to file. Individual and faceted plots have a different API (figure
    # vs fig) so we get around this using a try statement:
    if savefig_path: 
        
        print(f'Exporting image to {savefig_path}')
        
        try:
            img.fig.savefig(savefig_path, **savefig_kwargs)
        except:
            img.figure.savefig(savefig_path, **savefig_kwargs)

            
def map_shapefile(gdf, colormap=mpl.cm.YlOrRd, weight=2, default_zoom=13):
    
    def n_colors(n, colormap=colormap):
        data = np.linspace(0.0,1.0,n)
        c = [mpl.colors.rgb2hex(d[0:3]) for d in colormap(data)]
        return c

    def data_to_colors(data, colormap=colormap):
        c = [mpl.colors.rgb2hex(d[0:3]) for d in colormap(mpl.colors.Normalize()(data))]
        return c
        
    def click_handler(event=None, id=None, properties=None, type=None, coordinates=None):
        try:
            datasetID = properties['time']
            print(datasetID)
        except:
            pass
    
    # Convert to WGS 84 and geojson format
    gdf_wgs84 = gdf.to_crs(epsg=4326)
    data = gdf_wgs84.__geo_interface__    
    
    # For each feature in dataset, append colour values
    n_features = len(data['features'])
    colors = n_colors(n_features)
    
    for feature, color in zip(data['features'], colors):
        feature['properties']['style'] = {'color': color, 'weight': weight, 
                                          'fillColor': color, 'fillOpacity': 1.0}

    # Get centroid to focus map on
    lon, lat = gdf_wgs84.unary_union.centroid.coords.xy 
    
    # Plot map and add geojson layers
    m = Map(center=(lat[0], lon[0]), 
            zoom=default_zoom, 
            basemap=basemaps.Esri.WorldImagery, 
            layout=dict(width='800px', height='600px'))
    feature_layer = GeoJSON(data=data)
    feature_layer.on_click(click_handler)
    m.add_layer(feature_layer)
    
    return m


def interpolate_2d(ds, x_coords, y_coords, z_coords, 
                 method='linear', fill_nearest=False, sigma=None):
    
    '''
    This function takes points with X, Y and Z coordinates, and interpolates Z-values
    across the extent of an existing xarray dataset. This can be useful for producing 
    smooth surfaces from point data that can be compared directly against satellite
    data derived from an OpenDataCube query.
    
    Last modified: August 2019
    Author: Robbi Bishop-Taylor
    
    Parameters
    ----------  
    ds_array : xarray DataArray or Dataset
        A two-dimensional or multi-dimensional array from which x and y dimensions will be 
        copied and used for the area in which to interpolate point data. 
    x_coords : numpy array
        An array containing X coordinates for all points (e.g. longitudes). 
    y_coords : numpy array
        An array containing Y coordinates for all points (e.g. latitudes).
    z_coords : numpy array
        An array containing Z coordinates for all points (e.g. elevations). These are the 
        values you wish to interpolate between.
    method : string, optional
        The method used to interpolate between point values. This string is passed to 
        `scipy.interpolate.griddata`; the default is 'linear' and options include
        'linear', 'nearest' and 'cubic'.
    fill_nearest : boolean, optional
        A boolean value indicating whether to fill NaN areas outside of the extent of 
        the input X and Y coordinates with the value of the nearest pixel. By default,
        `scipy.interpolate.griddata` only returns interpolated values for the convex hull
        of the of the input points, so this variable can be used to provide results for
        all pixels instead. Warning: this can produce significant artefacts for areas
        located far from the nearest point.
    sigma : None or int, optional
        An optional integer value can be provided to smooth the interpolated surface
        using a guassian filter. Higher values of sigma result in a smoother surface
        that may loose some of the detail in the original interpolated layer.        
      
    Returns
    -------
    interp_2d_array : xarray DataArray
        An xarray DataArray containing with x and y coordinates copied from `ds_array`,
        and Z-values interpolated from the points data. 
        
    '''
    
    # Extract xy and elev points
    points_xy = np.vstack([x_coords, y_coords]).T

    # Create grid to interpolate into
    grid_y, grid_x = np.meshgrid(ds.x, ds.y)  

    # Interpolate x, y and z values using linear/TIN interpolation
    out = scipy.interpolate.griddata(points=points_xy, 
                                     values=z_coords, 
                                     xi=(grid_y, grid_x), 
                                     method=method)

    # Calculate nearest
    if fill_nearest:
        
        nearest_inds = nd.distance_transform_edt(input=np.isnan(out), 
                                                 return_distances=False, 
                                                 return_indices=True)
        out = out[tuple(nearest_inds)]
        
    # Apply guassian filter        
    if sigma:

        out = nd.filters.gaussian_filter(out, sigma=sigma)
        
    # Create xarray dataarray from the data
    interp_2d_array = xr.DataArray(out, coords=[ds.y, ds.x], dims=['y', 'x']) 
        
    return interp_2d_array


def contours_to_arrays(gdf, col):
    
    '''
    This function converts a polyline shapefile into an array with three
    columns giving the X, Y and Z coordinates of each vertex. This data
    can then be used as an input to interpolation procedures (e.g. using a
    function like `interpolate_2d`.
    
    Last modified: August 2019
    Author: Robbi Bishop-Taylor
    
    Parameters
    ----------  
    gdf : Geopandas GeoDataFrame
        A GeoPandas GeoDataFrame of lines to convert into point coordinates.
    col : str
        A string giving the name of the GeoDataFrame field to use as Z-values.
        
    Returns
    -------
    A numpy array with three columns giving the X, Y and Z coordinates of each
    vertex in the input GeoDataFrame.
        
    '''    
    

    coords_zvals = []

    for i in range(0, len(gdf)):

        val = gdf.iloc[i][col]

        try:
            coords = np.concatenate([np.vstack(x.coords.xy).T for x in gdf.iloc[i].geometry])

        except:
            coords = np.vstack(gdf.iloc[i].geometry.coords.xy).T

        coords_zvals.append(np.column_stack((coords, np.full(np.shape(coords)[0], fill_value=val))))

    return np.concatenate(coords_zvals)

            