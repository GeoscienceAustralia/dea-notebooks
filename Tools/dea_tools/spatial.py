## dea_spatialtools.py
'''
Tools for spatially manipulating Digital Earth Australia data.

License: The code in this notebook is licensed under the Apache License, 
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth 
Australia data is licensed under the Creative Commons by Attribution 4.0 
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data 
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack 
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) 
using the `open-data-cube` tag (you can view previously asked questions 
here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, file one on 
Github: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new

Last modified: November 2022

'''

# Import required packages
import dask
import fiona
import warnings
import collections
import odc.geo.xr
import numpy as np
import xarray as xr
import geopandas as gpd
import rasterio.features
import scipy.interpolate
import multiprocessing as mp
from scipy import ndimage as nd
from skimage.measure import label
from rasterstats import zonal_stats
from skimage.measure import find_contours
from geopy.geocoders import Nominatim
from datacube.utils.cog import write_cog
from datacube.utils.geometry import assign_crs
from datacube.utils.geometry import CRS, Geometry
from shapely.geometry import LineString, MultiLineString, shape, mapping


def _da_to_geo(da, crs):
    """
    Helper function that uses `odc-geo` to ensure that an 
    `xarray.DataArray` has a GeoBox and .odc.* accessor. 
    This is used to ensure that spatial information can be 
    consistently accessed from any input array.
    
    If `da` has missing Coordinate Reference System (CRS)
    information, this can be supplied using the `crs` param.
    """
    
    # Import the odc-geo package to add `.odc.x` attributes
    # to our input xr.DataArray
    import odc.geo.xr

    # If a CRS is not found, use custom provided CRS
    if da.odc.crs is None and crs is not None:
        da = da.odc.assign_crs(crs)
    elif da.odc.crs is None and crs is None:
        raise Exception(
            "Unable to determine `da`'s coordinate "
            "reference system (CRS). Please provide a "
            "CRS using the `crs` parameter "
            "(e.g. `crs='EPSG:3577'`)."
        )
        
    return da


def xr_vectorize(
    da,
    attribute_col=None,
    crs=None,
    dtype="float32",
    output_path=None,
    verbose=True,
    **rasterio_kwargs
):
    """
    Vectorises a raster ``xarray.DataArray`` into a vector
    ``geopandas.GeoDataFrame``.

    Parameters
    ----------
    da : xarray.DataArray
        The input ``xarray.DataArray`` data to vectorise.
    attribute_col : str, optional
        Name of the attribute column in the resulting
        ``geopandas.GeoDataFrame``. Values from ``da`` converted
        to polygons will be assigned to this column. If None, 
        the column name will default to 'attribute'.
    crs : str or CRS object, optional
        If ``da``'s coordinate reference system (CRS) cannot be
        determined, provide a CRS using this parameter.
        (e.g. 'EPSG:3577').
    dtype : str, optional
         Data type  of  must be one of int16, int32, uint8, uint16,
         or float32
    output_path : string, optional
        Provide an optional string file path to export the vectorised
        data to file. Supports any vector file formats supported by
        ``geopandas.GeoDataFrame.to_file()``.
    verbose : bool, optional
        Print debugging messages. Default True.
    **rasterio_kwargs :
        A set of keyword arguments to ``rasterio.features.shapes``.
        Can include `mask` and `connectivity`.

    Returns
    -------
    gdf : geopandas.GeoDataFrame

    """
    
    # Add GeoBox and odc.* accessor to array using `odc-geo`
    da = _da_to_geo(da, crs)

    # Run the vectorizing function
    vectors = rasterio.features.shapes(
        source=da.data.astype(dtype), transform=da.odc.transform, **rasterio_kwargs
    )

    # Convert the generator into a list
    vectors = list(vectors)

    # Extract the polygon coordinates and values from the list
    polygons = [polygon for polygon, value in vectors]
    values = [value for polygon, value in vectors]

    # Convert polygon coordinates into polygon shapes
    polygons = [shape(polygon) for polygon in polygons]

    # Create a geopandas dataframe populated with the polygon shapes
    attribute_name = attribute_col if attribute_col is not None else 'attribute'
    gdf = gpd.GeoDataFrame(data={attribute_name: values}, 
                           geometry=polygons, 
                           crs=da.odc.crs)

    # If a file path is supplied, export to file
    if output_path is not None:
        if verbose: print(f"Exporting vector data to {output_path}")
        gdf.to_file(output_path)

    return gdf


def xr_rasterize(gdf,
                 da,
                 attribute_col=None,
                 crs=None,
                 name=None,
                 output_path=None,
                 verbose=True,
                 **rasterio_kwargs):    
    """
    Rasterizes a vector ``geopandas.GeoDataFrame`` into a 
    raster ``xarray.DataArray``.
  
    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        A ``geopandas.GeoDataFrame`` object containing the vector
        data you want to rasterise.
    da : xarray.DataArray or xarray.Dataset
        The shape, coordinates, dimensions, and transform of this object 
        are used to define the array that ``gdf`` is rasterized into. 
        It effectively provides a spatial template.
    attribute_col : string, optional
        Name of the attribute column in ``gdf`` containing values for
        each vector feature that will be rasterized. If None, the 
        output will be a boolean array of 1's and 0's.
    crs : str or CRS object, optional
        If ``da``'s coordinate reference system (CRS) cannot be
        determined, provide a CRS using this parameter.
        (e.g. 'EPSG:3577').
    name : str, optional
        An optional name used for the output ``xarray.DataArray`.
    output_path : string, optional
        Provide an optional string file path to export the rasterized
        data as a GeoTIFF file.
    verbose : bool, optional
        Print debugging messages. Default True.
    **rasterio_kwargs : 
        A set of keyword arguments to ``rasterio.features.rasterize``.
        Can include: 'all_touched', 'merge_alg', 'dtype'.
    
    Returns
    -------
    da_rasterized : xarray.DataArray
        The rasterized vector data.
    """
    
    # Add GeoBox and odc.* accessor to array using `odc-geo`
    da = _da_to_geo(da, crs)

    # Reproject vector data to raster's CRS
    gdf_reproj = gdf.to_crs(crs=da.odc.crs)

    # If an attribute column is specified, rasterise using vector 
    # attribute values. Otherwise, rasterise into a boolean array
    if attribute_col is not None:        
        # Use the geometry and attributes from `gdf` to create an iterable
        shapes = zip(gdf_reproj.geometry, gdf_reproj[attribute_col])
    else:
        # Use geometry directly (will produce a boolean numpy array)
        shapes = gdf_reproj.geometry

    # Rasterise shapes into a numpy array
    im = rasterio.features.rasterize(
        shapes=shapes,
        out_shape=da.odc.geobox.shape,
        transform=da.odc.geobox.transform,
        **rasterio_kwargs,
    )

    # Convert numpy array to a full xarray.DataArray
    # and set array name if supplied
    da_rasterized = odc.geo.xr.wrap_xr(im=im, 
                                       gbox=da.odc.geobox)
    da_rasterized.rename(name)
    
    # If a file path is supplied, export to file
    if output_path is not None:
        if verbose: print(f"Exporting raster data to {output_path}")
        write_cog(da_rasterized, output_path, overwrite=True)
    
    return da_rasterized


def subpixel_contours(da,
                      z_values=[0.0],
                      crs=None,
                      attribute_df=None,
                      output_path=None,
                      min_vertices=2,
                      dim='time',
                      errors='ignore',
                      verbose=True):
    
    """
    Uses `skimage.measure.find_contours` to extract multiple z-value 
    contour lines from a two-dimensional array (e.g. multiple elevations
    from a single DEM), or one z-value for each array along a specified 
    dimension of a multi-dimensional array (e.g. to map waterlines 
    across time by extracting a 0 NDWI contour from each individual 
    timestep in an xarray timeseries).    
    
    Contours are returned as a geopandas.GeoDataFrame with one row per 
    z-value or one row per array along a specified dimension. The 
    `attribute_df` parameter can be used to pass custom attributes 
    to the output contour features.
    
    Last modified: November 2022
    
    Parameters
    ----------  
    da : xarray DataArray
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
    crs : string or CRS object, optional
        If ``da``'s coordinate reference system (CRS) cannot be
        determined, provide a CRS using this parameter.
        (e.g. 'EPSG:3577').
    output_path : string, optional
        The path and filename for the output shapefile.
    attribute_df : pandas.Dataframe, optional
        A pandas.Dataframe containing attributes to pass to the output
        contour features. The dataframe must contain either the same 
        number of rows as supplied `z_values` (in 'multiple z-value, 
        single array' mode), or the same number of rows as the number 
        of arrays along the `dim` dimension ('single z-value, multiple 
        arrays mode').
    min_vertices : int, optional
        The minimum number of vertices required for a contour to be 
        extracted. The default (and minimum) value is 2, which is the 
        smallest number required to produce a contour line (i.e. a start
        and end point). Higher values remove smaller contours, 
        potentially removing noise from the output dataset.
    dim : string, optional
        The name of the dimension along which to extract contours when 
        operating in 'single z-value, multiple arrays' mode. The default
        is 'time', which extracts contours for each array along the time
        dimension.
    errors : string, optional
        If 'raise', then any failed contours will raise an exception.
        If 'ignore' (the default), a list of failed contours will be
        printed. If no contours are returned, an exception will always
        be raised.
    verbose : bool, optional
        Print debugging messages. Default is True.
        
    Returns
    -------
    output_gdf : geopandas geodataframe
        A geopandas geodataframe object with one feature per z-value 
        ('single array, multiple z-values' mode), or one row per array 
        along the dimension specified by the `dim` parameter ('single 
        z-value, multiple arrays' mode). If `attribute_df` was 
        provided, these values will be included in the shapefile's 
        attribute table.
    """

    def _contours_to_multiline(da_i, z_value, min_vertices=2):
        '''
        Helper function to apply marching squares contour extraction
        to an array and return a data as a shapely MultiLineString.
        The `min_vertices` parameter allows you to drop small contours 
        with less than X vertices.
        '''
        
        # Extracts contours from array, and converts each discrete
        # contour into a Shapely LineString feature. If the function 
        # returns a KeyError, this may be due to an unresolved issue in
        # scikit-image: https://github.com/scikit-image/scikit-image/issues/4830
        try:            
            line_features = [LineString(i[:,[1, 0]]) 
                             for i in find_contours(da_i.data, z_value) 
                             if i.shape[0] > min_vertices]
        except KeyError:
            line_features = [LineString(i[:,[1, 0]]) 
                             for i in find_contours(da_i.data, z_value + 1e-12) 
                             if i.shape[0] > min_vertices]

        # Output resulting lines into a single combined MultiLineString
        return MultiLineString(line_features)


    # Add GeoBox and odc.* accessor to array using `odc-geo`
    da = _da_to_geo(da, crs)

    # If z_values is supplied is not a list, convert to list:
    z_values = z_values if (isinstance(z_values, list) or 
                            isinstance(z_values, np.ndarray)) else [z_values]
    
    # If dask collection, load into memory
    if dask.is_dask_collection(da):
        if verbose:
            print(f'Loading data into memory using Dask')
        da = da.compute()

    # Test number of dimensions in supplied data array
    if len(da.shape) == 2:
        if verbose:
            print(f'Operating in multiple z-value, single array mode')
        dim = 'z_value'
        contour_arrays = {str(i)[0:10]: 
                          _contours_to_multiline(da, i, min_vertices) 
                          for i in z_values}    

    else:

        # Test if only a single z-value is given when operating in 
        # single z-value, multiple arrays mode
        if verbose:
            print(f'Operating in single z-value, multiple arrays mode')
        if len(z_values) > 1:
            raise ValueError('Please provide a single z-value when operating '
                             'in single z-value, multiple arrays mode')

        contour_arrays = {str(i)[0:10]: 
                          _contours_to_multiline(da_i, z_values[0], min_vertices) 
                          for i, da_i in da.groupby(dim)}

    # If attributes are provided, add the contour keys to that dataframe
    if attribute_df is not None:

        try:
            attribute_df.insert(0, dim, contour_arrays.keys())
        except ValueError:

            raise ValueError("One of the following issues occured:\n\n"
                             "1) `attribute_df` contains a different number of "
                             "rows than the number of supplied `z_values` ("
                             "'multiple z-value, single array mode')\n"
                             "2) `attribute_df` contains a different number of "
                             "rows than the number of arrays along the `dim` "
                             "dimension ('single z-value, multiple arrays mode')")

    # Otherwise, use the contour keys as the only main attributes
    else:
        attribute_df = list(contour_arrays.keys())

    # Convert output contours to a geopandas.GeoDataFrame
    contours_gdf = gpd.GeoDataFrame(data=attribute_df, 
                                    geometry=list(contour_arrays.values()),
                                    crs=da.odc.crs)   

    # Define affine and use to convert array coords to geographic coords.
    # We need to add 0.5 x pixel size to the x and y to obtain the centre 
    # point of our pixels, rather than the top-left corner
    affine = da.odc.geobox.transform
    shapely_affine = [affine.a, affine.b, affine.d, affine.e, 
                      affine.xoff + affine.a / 2.0, 
                      affine.yoff + affine.e / 2.0]
    contours_gdf['geometry'] = contours_gdf.affine_transform(shapely_affine)

    # Rename the data column to match the dimension
    contours_gdf = contours_gdf.rename({0: dim}, axis=1)

    # Drop empty timesteps
    empty_contours = contours_gdf.geometry.is_empty
    failed = ', '.join(map(str, contours_gdf[empty_contours][dim].to_list()))
    contours_gdf = contours_gdf[~empty_contours]

    # Raise exception if no data is returned, or if any contours fail
    # when `errors='raise'. Otherwise, print failed contours
    if empty_contours.all() and errors == 'raise':
        raise RuntimeError("Failed to generate any valid contours; verify that "
                           "values passed to `z_values` are valid and present "
                           "in `da`")
    elif empty_contours.all() and errors == 'ignore':
        if verbose:
            print ("Failed to generate any valid contours; verify that "
                    "values passed to `z_values` are valid and present "
                    "in `da`")
    elif empty_contours.any() and errors == 'raise':
        raise Exception(f'Failed to generate contours: {failed}')
    elif empty_contours.any() and errors == 'ignore':
        if verbose:
            print(f'Failed to generate contours: {failed}')

    # If asked to write out file, test if geojson or shapefile
    if output_path and output_path.endswith('.geojson'):
        if verbose:
            print(f'Writing contours to {output_path}')
        contours_gdf.to_crs('EPSG:4326').to_file(filename=output_path)

    if output_path and output_path.endswith('.shp'):
        if verbose:
            print(f'Writing contours to {output_path}')
        contours_gdf.to_file(filename=output_path)
        
    return contours_gdf


def interpolate_2d(ds, 
                   x_coords, 
                   y_coords, 
                   z_coords, 
                   method='linear',
                   factor=1,
                   verbose=False,
                   **kwargs):
    
    """
    This function takes points with X, Y and Z coordinates, and 
    interpolates Z-values across the extent of an existing xarray 
    dataset. This can be useful for producing smooth surfaces from point
    data that can be compared directly against satellite data derived 
    from an OpenDataCube query.
    
    Supported interpolation methods include 'linear', 'nearest' and
    'cubic (using `scipy.interpolate.griddata`), and 'rbf' (using 
    `scipy.interpolate.Rbf`).
    
    Last modified: February 2020
    
    Parameters
    ----------  
    ds : xarray DataArray or Dataset
        A two-dimensional or multi-dimensional array from which x and y 
        dimensions will be copied and used for the area in which to 
        interpolate point data. 
    x_coords, y_coords : numpy array
        Arrays containing X and Y coordinates for all points (e.g. 
        longitudes and latitudes).
    z_coords : numpy array
        An array containing Z coordinates for all points (e.g. 
        elevations). These are the values you wish to interpolate 
        between.
    method : string, optional
        The method used to interpolate between point values. This string
        is either passed to `scipy.interpolate.griddata` (for 'linear', 
        'nearest' and 'cubic' methods), or used to specify Radial Basis 
        Function interpolation using `scipy.interpolate.Rbf` ('rbf').
        Defaults to 'linear'.
    factor : int, optional
        An optional integer that can be used to subsample the spatial 
        interpolation extent to obtain faster interpolation times, then
        up-sample this array back to the original dimensions of the 
        data as a final step. For example, setting `factor=10` will 
        interpolate data into a grid that has one tenth of the 
        resolution of `ds`. This approach will be significantly faster 
        than interpolating at full resolution, but will potentially 
        produce less accurate or reliable results.
    verbose : bool, optional
        Print debugging messages. Default False.
    **kwargs : 
        Optional keyword arguments to pass to either 
        `scipy.interpolate.griddata` (if `method` is 'linear', 'nearest' 
        or 'cubic'), or `scipy.interpolate.Rbf` (is `method` is 'rbf').
      
    Returns
    -------
    interp_2d_array : xarray DataArray
        An xarray DataArray containing with x and y coordinates copied 
        from `ds_array`, and Z-values interpolated from the points data. 
    """
    
    # Extract xy and elev points
    points_xy = np.vstack([x_coords, y_coords]).T
    
    # Extract x and y coordinates to interpolate into. 
    # If `factor` is greater than 1, the coordinates will be subsampled 
    # for faster run-times. If the last x or y value in the subsampled 
    # grid aren't the same as the last x or y values in the original 
    # full resolution grid, add the final full resolution grid value to 
    # ensure data is interpolated up to the very edge of the array
    if ds.x[::factor][-1].item() == ds.x[-1].item():
        x_grid_coords = ds.x[::factor].values
    else:
        x_grid_coords = ds.x[::factor].values.tolist() + [ds.x[-1].item()]
        
    if ds.y[::factor][-1].item() == ds.y[-1].item():
        y_grid_coords = ds.y[::factor].values
    else:
        y_grid_coords = ds.y[::factor].values.tolist() + [ds.y[-1].item()]

    # Create grid to interpolate into
    grid_y, grid_x = np.meshgrid(x_grid_coords, y_grid_coords)
    
    # Apply scipy.interpolate.griddata interpolation methods
    if method in ('linear', 'nearest', 'cubic'):
        
        # Interpolate x, y and z values 
        interp_2d = scipy.interpolate.griddata(points=points_xy, 
                                               values=z_coords, 
                                               xi=(grid_y, grid_x), 
                                               method=method,
                                               **kwargs)
    
    # Apply Radial Basis Function interpolation
    elif method == 'rbf':

        # Interpolate x, y and z values 
        rbf = scipy.interpolate.Rbf(x_coords, y_coords, z_coords, **kwargs)  
        interp_2d = rbf(grid_y, grid_x)

    # Create xarray dataarray from the data and resample to ds coords
    interp_2d_da = xr.DataArray(interp_2d, 
                                coords=[y_grid_coords, x_grid_coords], 
                                dims=['y', 'x'])
    
    # If factor is greater than 1, resample the interpolated array to
    # match the input `ds` array
    if factor > 1: 
        interp_2d_da = interp_2d_da.interp_like(ds)   

    return interp_2d_da


def contours_to_arrays(gdf, col):
    
    """
    This function converts a polyline shapefile into an array with three
    columns giving the X, Y and Z coordinates of each vertex. This data
    can then be used as an input to interpolation procedures (e.g. using 
    a function like `interpolate_2d`.
    
    Last modified: October 2021
    
    Parameters
    ----------  
    gdf : Geopandas GeoDataFrame
        A GeoPandas GeoDataFrame of lines to convert into point 
        coordinates.
    col : str
        A string giving the name of the GeoDataFrame field to use as 
        Z-values.
        
    Returns
    -------
    A numpy array with three columns giving the X, Y and Z coordinates 
    of each vertex in the input GeoDataFrame.
        
    """        

    coords_zvals = []

    for i in range(0, len(gdf)):

        val = gdf.iloc[i][col]

        try:
            coords = np.concatenate([np.vstack(x.coords.xy).T 
                                     for x in gdf.iloc[i].geometry.geoms])
        except:
            coords = np.vstack(gdf.iloc[i].geometry.coords.xy).T

        coords_zvals.append(np.column_stack((coords, 
                                             np.full(np.shape(coords)[0], 
                                                     fill_value=val))))

    return np.concatenate(coords_zvals)


def largest_region(bool_array, **kwargs):
    
    '''
    Takes a boolean array and identifies the largest contiguous region of 
    connected True values. This is returned as a new array with cells in 
    the largest region marked as True, and all other cells marked as False.
    
    Parameters
    ----------  
    bool_array : boolean array
        A boolean array (numpy or xarray.DataArray) with True values for
        the areas that will be inspected to find the largest group of 
        connected cells
    **kwargs : 
        Optional keyword arguments to pass to `measure.label`
        
    Returns
    -------
    largest_region : boolean array
        A boolean array with cells in the largest region marked as True, 
        and all other cells marked as False.       
        
    '''
    
    # First, break boolean array into unique, discrete regions/blobs
    blobs_labels = label(bool_array, background=0, **kwargs)
    
    # Count the size of each blob, excluding the background class (0)
    ids, counts = np.unique(blobs_labels[blobs_labels > 0], 
                            return_counts=True) 
    
    # Identify the region ID of the largest blob
    largest_region_id = ids[np.argmax(counts)]
    
    # Produce a boolean array where 1 == the largest region
    largest_region = blobs_labels == largest_region_id
    
    return largest_region


def transform_geojson_wgs_to_epsg(geojson, EPSG):
    """
    Takes a geojson dictionary and converts it from WGS84 (EPSG:4326) to desired EPSG

    Parameters
    ----------
    geojson: dict
        a geojson dictionary containing a 'geometry' key, in WGS84 coordinates
    EPSG: int
        numeric code for the EPSG coordinate referecnce system to transform into

    Returns
    -------
    transformed_geojson: dict
        a geojson dictionary containing a 'coordinates' key, in the desired CRS

    """
    gg = Geometry(geojson['geometry'], CRS('epsg:4326'))
    gg = gg.to_crs(CRS(f'epsg:{EPSG}'))
    return gg.__geo_interface__


def zonal_stats_parallel(shp,
                         raster,
                         statistics,
                         out_shp,
                         ncpus,
                         **kwargs):

    """
    Summarizing raster datasets based on vector geometries in parallel.
    Each cpu recieves an equal chunk of the dataset. 
    Utilizes the perrygeo/rasterstats package.
    
    Parameters
    ----------
    shp : str
        Path to shapefile that contains polygons over
        which zonal statistics are calculated
    raster: str
        Path to the raster from which the statistics are calculated.
        This can be a virtual raster (.vrt).
    statistics: list
        list of statistics to calculate. e.g.
            ['min', 'max', 'median', 'majority', 'sum']
    out_shp: str
        Path to export shapefile containing zonal statistics.
    ncpus: int
        number of cores to parallelize the operations over. 
    kwargs: 
        Any other keyword arguments to rasterstats.zonal_stats()
        See https://github.com/perrygeo/python-rasterstats for
        all options
            
    Returns
    -------
    Exports a shapefile to disk containing the zonal statistics requested
    
    """
    
    #yields n sized chunks from list l (used for splitting task to multiple processes)
    def chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    #calculates zonal stats and adds results to a dictionary
    def worker(z,raster,d):	
        z_stats = zonal_stats(z,raster,stats=statistics,**kwargs)
        for i in range(0,len(z_stats)):
            d[z[i]['id']]=z_stats[i]

    #write output polygon
    def write_output(zones, out_shp,d):
        
        #copy schema and crs from input and add new fields for each statistic     
        schema = zones.schema.copy()
        crs = zones.crs
        for stat in statistics:
            schema['properties'][stat] = 'float'

        with fiona.open(out_shp, 'w', 'ESRI Shapefile', schema, crs) as output:
            for elem in zones:
                for stat in statistics:
                    elem['properties'][stat]=d[elem['id']][stat]
                output.write({'properties':elem['properties'],'geometry': mapping(shape(elem['geometry']))})
    
    with fiona.open(shp) as zones:
        jobs = []

        # create manager dictionary (polygon ids=keys, stats=entries)
        # where multiple processes can write without conflicts
        man = mp.Manager()	
        d = man.dict()	

        #split zone polygons into 'ncpus' chunks for parallel processing 
        # and call worker() for each
        split = chunks(zones, len(zones)//ncpus)
        for z in split:
            p = mp.Process(target=worker,args=(z, raster,d))
            p.start()
            jobs.append(p)

        #wait that all chunks are finished
        [j.join() for j in jobs]

        write_output(zones,out_shp,d)


def reverse_geocode(coords, site_classes=None, state_classes=None):
    
    """
    Takes a latitude and longitude coordinate, and performs a reverse 
    geocode to return a plain-text description of the location in the 
    form:
        
        Site, State
        
    E.g.: `reverse_geocode(coords=(-35.282163, 149.128835))`
    
        'Canberra, Australian Capital Territory'

    Parameters
    ----------
    coords : tuple of floats
        A tuple of (latitude, longitude) coordinates used to perform 
        the reverse geocode.
    site_classes : list of strings, optional
        A list of strings used to define the site part of the plain 
        text location description. Because the contents of the geocoded 
        address can vary greatly depending on location, these strings
        are tested against the address one by one until a match is made.
        Defaults to: `['city', 'town', 'village', 'suburb', 'hamlet', 
                       'county', 'municipality']`.      
    state_classes : list of strings, optional
        A list of strings used to define the state part of the plain 
        text location description. These strings are tested against the 
        address one by one until a match is made. Defaults to: 
        `['state', 'territory']`.

    Returns
    -------
    If a valid geocoded address is found, a plain text location 
    description will be returned:
    
        'Site, State'
    
    If no valid address is found, formatted coordinates will be returned
    instead:
    
        'XX.XX S, XX.XX E'   

    """

    # Run reverse geocode using coordinates
    geocoder = Nominatim(user_agent='Digital Earth Australia')
    out = geocoder.reverse(coords)
    
    # Create plain text-coords as fall-back
    lat = f'{-coords[0]:.2f} S' if coords[0] < 0 else f'{coords[0]:.2f} N'
    lon = f'{-coords[1]:.2f} W' if coords[1] < 0 else f'{coords[1]:.2f} E'

    try:
        
        # Get address from geocoded data
        address = out.raw['address']

        # Use site and state classes if supplied; else use defaults
        default_site_classes = ['city', 'town', 'village', 'suburb', 'hamlet', 
                                'county', 'municipality']
        default_state_classes = ['state', 'territory']
        site_classes = site_classes if site_classes else default_site_classes
        state_classes = state_classes if state_classes else default_state_classes

        # Return the first site or state class that exists in address dict
        site = next((address[k] for k in site_classes if k in address), None)
        state = next((address[k] for k in state_classes if k in address), None)
        
        # If site and state exist in the data, return this.
        # Otherwise, return N/E/S/W coordinates.
        if site and state:

            # Return as site, state formatted string
            return f'{site}, {state}'
        
        else:
            
            # If no geocoding result, return N/E/S/W coordinates
            print('No valid geocoded location; returning coordinates instead')
            return f'{lat}, {lon}'
              
    except (KeyError, AttributeError):

        # If no geocoding result, return N/E/S/W coordinates
        print('No valid geocoded location; returning coordinates instead')
        return f'{lat}, {lon}'


def hillshade(dem, elevation, azimuth, vert_exag=1, dx=30, dy=30):
    """
    Calculate hillshade from an input Digital Elevation Model
    (DEM) array and a sun elevation and azimith.

    Parameters:
    -----------
    dem : numpy.array
        A 2D Digital Elevation Model array.
    elevation : int or float
        Sun elevation (0-90, degrees up from horizontal).
    azimith : int or float
        Sun azimuth (0-360, degrees clockwise from north).
    vert_exag : int or float, optional
        The amount to exaggerate the elevation values by
        when calculating illumination. This can be used either
        to correct for differences in units between the x-y coordinate
        system and the elevation coordinate system (e.g. decimal
        degrees vs. meters) or to exaggerate or de-emphasize
        topographic effects.
    dx : int or float, optional
        The x-spacing (columns) of the input DEM. This
        is typically the spatial resolution of the DEM.
    dy : int or float, optional
        The y-spacing (rows) of the input input DEM. This
        is typically the spatial resolution of the DEM.

    Returns:
    --------
    hs : numpy.array
        A 2D hillshade array with values between 0-1, where
        0 is completely in shadow and 1 is completely
        illuminated.
    """

    from matplotlib.colors import LightSource

    hs = LightSource(azdeg=azimuth, altdeg=elevation).hillshade(
        dem, vert_exag=vert_exag, dx=dx, dy=dy
    )
    return hs


def sun_angles(dc, query):
    """
    For a given spatiotemporal query, calculate mean sun
    azimuth and elevation for each satellite observation, and
    return these as a new `xarray.Dataset` with 'sun_elevation'
    and 'sun_azimuth' variables.

    Parameters:
    -----------
    dc : datacube.Datacube object
        Datacube instance used to load data.
    query : dict
        A dictionary containing query parameters used to identify
        satellite observations and load metadata.

    Returns:
    --------
    sun_angles_ds : xarray.Dataset
        An `xarray.set` containing a 'sun_elevation' and
        'sun_azimuth' variables.
    """

    from datacube.api.query import query_group_by
    from datacube.model.utils import xr_apply

    # Identify satellite datasets and group outputs using the
    # same approach used to group satellite imagery (i.e. solar day)
    gb = query_group_by(**query)
    datasets = dc.find_datasets(**query)
    dataset_array = dc.group_datasets(datasets, gb)

    # Load and take the mean of metadata from each product
    sun_azimuth = xr_apply(
        dataset_array,
        lambda t, dd: np.mean([d.metadata.eo_sun_azimuth for d in dd]),
        dtype=float,
    )
    sun_elevation = xr_apply(
        dataset_array,
        lambda t, dd: np.mean([d.metadata.eo_sun_elevation for d in dd]),
        dtype=float,
    )

    # Combine into new xarray.Dataset
    sun_angles_ds = xr.merge(
        [sun_elevation.rename("sun_elevation"), sun_azimuth.rename("sun_azimuth")]
    )

    return sun_angles_ds
