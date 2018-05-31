## DEADataHandling.py
'''
This file contains a set of python functions for handling data within DEA. If a function does not use 
DEA functionality (for example, dc.load or xarrays), it may be better suited for inclusion in SpatialTools.py.
Available functions:

    load_nbarx
    load_sentinel
    load_clearlandsat (also does fractional cover)
    tasseled_cap
    dataset_to_geotiff
    open_polygon_from_shapefile
    write_your_netcdf
    zonal_timeseries

Last modified: May 2018
Authors: Claire Krause, Robbi Bishop-Taylor, Bex Dunn

'''

# Load modules
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
import gdal
import numpy as np
import xarray as xr
import rasterio
import geopandas as gpd
import dask
# import rasterstats as rs

from datacube.utils import geometry
import fiona
import shapely.geometry
from datacube.storage.storage import write_dataset_to_netcdf

def load_nbarx(dc, sensor, query, product='nbart', bands_of_interest='', filter_pq=True):
    """
    Loads NBAR (Nadir BRDF Adjusted Reflectance) or NBAR-T (terrain corrected NBAR) data for a
    sensor, masks using pixel quality (PQ), then optionally filters out terrain -999s (for NBAR-T).
    Returns an xarray dataset and CRS and Affine objects defining map projection and geotransform

    Last modified: May 2018
    Author: Bex Dunn
    Modified by: Claire Krause, Robbi Bishop-Taylor, Bex Dunn

    inputs
    dc - Handle for the Datacube to import from. This allows you to also use dev environments
    if that have been imported into the environment.
    sensor - Options are 'ls5', 'ls7', 'ls8'
    query - A dict containing the query bounds. Can include lat/lon, time etc. 

    optional
    product - 'nbar' or 'nbart'. Defaults to nbart unless otherwise specified
    bands_of_interest - List of strings containing the bands to be read in; defaults to all bands,
                        options include 'red', 'green', 'blue', 'nir', 'swir1', 'swir2'
    filter_pq - boolean. Will filter clouds and saturated pixels using PQ unless set to False


    outputs
    ds - Extracted and optionally PQ filtered dataset
    crs - CRS object defining dataset coordinate reference system
    affine - Affine object defining dataset affine transformation
    """

    product_name = '{}_{}_albers'.format(sensor, product)
    mask_product = '{}_{}_albers'.format(sensor, 'pq')
    print('Loading {}'.format(product_name))

    # If bands of interest are given, assign measurements in dc.load call
    if bands_of_interest:

        ds = dc.load(product=product_name, measurements=bands_of_interest,
                     group_by='solar_day', **query)

    # If no bands of interest given, run without specifying measurements
    else:

        ds = dc.load(product=product_name, group_by='solar_day', **query)

    # Proceed if the resulting call returns data
    if ds.variables:

        crs = ds.crs
        affine = ds.affine
        print('Loaded {}'.format(product_name))

        # If pixel quality filtering is enabled, extract PQ data to use as mask
        if filter_pq:

            sensor_pq = dc.load(product=mask_product, fuse_func=ga_pq_fuser,
                                group_by='solar_day', **query)

            # If PQ call returns data, use to mask input data
            if sensor_pq.variables:
                print('Generating mask {}'.format(mask_product))
                good_quality = masking.make_mask(sensor_pq.pixelquality,
                                                 cloud_acca='no_cloud',
                                                 cloud_shadow_acca='no_cloud_shadow',
                                                 cloud_shadow_fmask='no_cloud_shadow',
                                                 cloud_fmask='no_cloud',
                                                 blue_saturated=False,
                                                 green_saturated=False,
                                                 red_saturated=False,
                                                 nir_saturated=False,
                                                 swir1_saturated=False,
                                                 swir2_saturated=False,
                                                 contiguous=True)

                # Apply mask to preserve only good data
                ds = ds.where(good_quality)

            ds.attrs['crs'] = crs
            ds.attrs['affine'] = affine

        # Replace nodata values with nans

            ds = masking.mask_invalid_data(ds)

        return ds, crs, affine

    else:

        print('Failed to load {}'.format(product_name))
        return None, None, None


def load_sentinel(dc, product, query, filter_cloud=True, **bands_of_interest):
    '''loads a sentinel granule product and masks using pq

    Last modified: March 2018
    Authors: Claire Krause, Bex Dunn

    This function requires the following be loaded:
    from datacube.helpers import ga_pq_fuser
    from datacube.storage import masking
    from datacube import Datacube

    inputs
    dc - handle for the Datacube to import from. This allows you to also use dev environments
	 if that have been imported into the environment.
    product - string containing the name of the sentinel product to load
    query - A dict containing the query bounds. Can include lat/lon, time etc

    optional:
    bands_of_interest - List of strings containing the bands to be read in.

    outputs
    ds - Extracted and pq filtered dataset
    crs - ds coordinate reference system
    affine - ds affine
    '''
    dataset = []
    print('loading {}'.format(product))
    if bands_of_interest:
        ds = dc.load(product=product, measurements=bands_of_interest,
                     group_by='solar_day', **query)
    else:
        ds = dc.load(product=product, group_by='solar_day', **query)
    if ds.variables:
        crs = ds.crs
        affine = ds.affine
        print('loaded {}'.format(product))
        if filter_cloud:
            print('making mask')
            clear_pixels = np.logical_and(ds.pixel_quality != 0, ds.pixel_quality != 2, 
                                          ds.pixel_quality != 3)
            ds = ds.where(clear_pixels)
        ds.attrs['crs'] = crs
        ds.attrs['affine'] = affine
    else:
        print('did not load {}'.format(product))

    if len(ds.variables) > 0:
        return ds, crs, affine
    else:
        return None


def load_clearlandsat(dc, query, sensors=['ls5', 'ls7', 'ls8'], bands_of_interest=None,
                      product='nbart', masked_prop=0.99, mask_dict=None, apply_mask=False):
    
    """
    Loads Landsat NBAR, NBART or FC25, and PQ data for multiple sensors (i.e. ls5, ls7, ls8), and returns a single 
    xarray dataset containing only observations that contain greater than a given proportion of clear pixels.    
  
    This function was designed to extract visually appealing time series of observations that are not
    affected by cloud, for example as an input to the `animated_timeseries` function from `DEAPlotting`.
    
    The proportion of clear pixels is calculated by summing the pixels that are flagged as being problematic
    in the Landsat PQ25 layer. By default only cloudy pixels or pixels without valid data in every band 
    are included in the calculation, but this can be customised using the `mask_dict` function.
    
    Last modified: May 2018
    Author: Robbi Bishop-Taylor, Bex Dunn
    
    :param dc: 
        A specific Datacube to import from, i.e. `dc = datacube.Datacube(app='Clear Landsat')`. This allows you to 
        also use development datacubes if they have been imported into the environment.
    
    :param query: 
        A dict containing the query bounds. Can include lat/lon, time etc. If no `time` query is given, the 
        function defaults to all timesteps available to all sensors (e.g. 1987-2018)

    :param sensors:
        An optional list of Landsat sensor names to load data for. Options are 'ls5', 'ls7', 'ls8'; defaults to all.

    :param product:
        An optional string specifying 'nbar', 'nbart' or 'fc'. Defaults to 'nbart'. For information on the difference, 
        see the 'GettingStartedWithLandsat5-7-8' or 'Introduction_to_Fractional_Cover' notebooks on DEA-notebooks.
        
    :param bands_of_interest:
        An optional list of strings containing the bands to be read in; options include 'red', 'green', 'blue', 
        'nir', 'swir1', 'swir2'; defaults to all available bands if no bands are specified.

    :param masked_prop:
        An optional float giving the minimum percentage of clear pixels required for a Landsat observation to be 
        loaded. Defaults to 0.99 (i.e. only return observations with less than 1% of unclear pixels).
            
    :param mask_dict:
        An optional dict of arguments to the `masking.make_mask` function that can be used to identify clear 
        observations from the PQ layer using alternative masking criteria. The default value of None masks out 
        pixels flagged as cloud by either the ACCA or Fmask alogorithms, and that have values for every band 
        (equivalent to: `mask_dict={'cloud_acca': 'no_cloud', 'cloud_fmask': 'no_cloud', 'contiguous': True}`.
        See the `Landsat5-7-8-PQ` notebook on DEA Notebooks for a list of all possible options.
        
    :param apply_mask:
        An optional boolean indicating whether resulting observations should have the PQ mask applied to filter
        out any remaining unclear cells. For example, if `masked_prop=0.99`, the filtered images may still contain
        up to 1% unclear/cloudy pixels. The default of False simply returns the resulting observations without
        masking out these pixels; True removes them using the mask. 
    
    :returns:
        An xarray dataset containing only Landsat observations that contain greater than `masked_prop`
        proportion of clear pixels.  
        
    :example:
    
    >>> # Import modules
    >>> import datacube     
    >>> 
    >>> # Define datacube to import from
    >>> dc = datacube.Datacube(app='Clear Landsat')
    >>> 
    >>> # Set up spatial and temporal query
    >>> query = {'x': (-191400.0, -183400.0),
    >>>          'y': (-1423460.0, -1415460.0),
    >>>          'time': ('2013-01-01', '2018-01-01'),
    >>>          'crs': 'EPSG:3577'}
    >>> 
    >>> # Load in red, green and blue bands for all clear Landsat observations with < 1% unclear values. 
    >>> combined_ds = load_clearlandsat(dc=dc, query=query, 
    >>>                                 bands_of_interest=['red', 'green', 'blue'], 
    >>>                                 masked_prop=0.99) 
    >>> combined_ds
        
    """
    

    # List to save results from each sensor
    filtered_sensors = []

    # Iterate through all sensors, returning only observations with > mask_prop clear pixels
    for sensor in sensors:
        
        try:
            
            # If bands of interest are given, assign measurements in dc.load call. This is
            # for compatibility with the existing dea-notebooks load_nbarx function.
            if bands_of_interest:
                
                # Lazily load Landsat data using dask              
                data = dc.load(product = '{}_{}_albers'.format(sensor, product),
                               measurements=bands_of_interest,
                               group_by = 'solar_day', 
                               dask_chunks={'time': 1},
                               **query)

            # If no bands of interest given, run without specifying measurements, and 
            # therefore return all available bands
            else:
                
                # Lazily load Landsat data using dask  
                data = dc.load(product = '{}_{}_albers'.format(sensor, product),
                               group_by = 'solar_day', 
                               dask_chunks={'time': 1},
                               **query)             

            # Load PQ data
            print('Loading {} PQ'.format(sensor))
            pq = dc.load(product = '{}_pq_albers'.format(sensor),
                         group_by = 'solar_day',
                         fuse_func=ga_pq_fuser,
                         **query)

            # Return only Landsat observations that have matching PQ data (this may
            # need to be improved, but seems to work in most cases)
            data = data.sel(time = pq.time, method='nearest')
            
            # If a custom dict is provided for mask_dict, use these values to make mask from PQ
            if mask_dict:
                
                # Mask PQ using custom values by unpacking mask_dict **kwarg
                good_quality = masking.make_mask(pq.pixelquality, **mask_dict)
                
            else:

                # Identify pixels with no clouds in either ACCA for Fmask
                good_quality = masking.make_mask(pq.pixelquality,
                                                 cloud_acca='no_cloud',
                                                 cloud_fmask='no_cloud',
                                                 contiguous=True)

            # Compute good data for each observation as a percentage of total array pixels
            data_perc = good_quality.sum(dim=['x', 'y']) / (good_quality.shape[1] * good_quality.shape[2])
            
            # Add data_perc data to Landsat dataset as a new xarray variable
            data['data_perc'] = xr.DataArray(data_perc, [('time', data.time)])

            # Filter and finally import data using dask
            filtered = data.where(data.data_perc >= masked_prop, drop=True)
            print('    Loading {} filtered {} timesteps'.format(len(filtered.time), sensor))
            filtered = filtered.compute()
            
            # Optionally apply mask (instead of only filtering)
            if apply_mask:
                filtered = filtered.where(good_quality)
            
            # Append result to list
            filtered_sensors.append(filtered)
        
        except:
            
            # If there is no data for sensor or if another error occurs:
            print('    Skipping {}'.format(sensor))

    # Concatenate all sensors into one big xarray dataset, and then sort by time
    print('Combining and sorting ls5, ls7 and ls8 data')
    combined_ds = xr.concat(filtered_sensors, dim='time')
    combined_ds = combined_ds.sortby('time')
                                                               
    #Filter to replace no data values with nans
    combined_ds = masking.mask_invalid_data(combined_ds)

    # Return combined dataset
    return combined_ds


def tasseled_cap(sensor_data, sensor, tc_bands=['greenness', 'brightness', 'wetness'],
                 drop=True):
    """
    Computes tasseled cap wetness, greenness and brightness bands from a six
    band xarray dataset, and returns a new xarray dataset with old bands
    optionally dropped.

    Coefficients for demonstration purposes only; sourced from:
    Landsat 5: https://doi.org/10.1016/0034-4257(85)90102-6
    Landsat 7: https://doi.org/10.1080/01431160110106113
    Landsat 8: https://doi.org/10.1080/2150704X.2014.915434

    :attr sensor_data: input xarray dataset with six Landsat bands
    :attr tc_bands: list of tasseled cap bands to compute
    (valid options: 'wetness', 'greenness','brightness'
    :attr sensor: Landsat sensor used for coefficient values
    (valid options: 'ls5', 'ls7', 'ls8')
    :attr drop: if 'drop = False', return all original Landsat bands

    :returns: xarray dataset with newly computed tasseled cap bands
    """

    # Copy input dataset
    output_array = sensor_data.copy(deep=True)

    # Coefficients for each tasseled cap band
    wetness_coeff = {'ls5': {'blue': 0.0315, 'green': 0.2021, 'red': 0.3102,
                             'nir': 0.1594, 'swir1': -0.6806, 'swir2': -0.6109},
                     'ls7': {'blue': 0.2626, 'green': 0.2141, 'red': 0.0926,
                             'nir': 0.0656, 'swir1': -0.7629, 'swir2': -0.5388},
                     'ls8': {'blue': 0.1511, 'green': 0.1973, 'red': 0.3283,
                             'nir': 0.3407, 'swir1': -0.7117, 'swir2': -0.4559}}

    greenness_coeff = {'ls5': {'blue': -0.1603, 'green': -0.2819, 'red': -0.4934,
                               'nir': 0.7940, 'swir1': -0.0002, 'swir2': -0.1446},
                       'ls7': {'blue': -0.3344, 'green': -0.3544, 'red': -0.4556,
                               'nir': 0.6966, 'swir1': -0.0242, 'swir2': -0.2630},
                       'ls8': {'blue': -0.2941, 'green': -0.2430, 'red': -0.5424,
                               'nir': 0.7276, 'swir1': -0.0713, 'swir2': -0.1608}}

    brightness_coeff = {'ls5': {'blue': 0.2043, 'green': 0.4158, 'red': 0.5524,
                                'nir': 0.5741, 'swir1': 0.3124, 'swir2': 0.2303},
                        'ls7': {'blue': 0.3561, 'green': 0.3972, 'red': 0.3904,
                                'nir': 0.6966, 'swir1': 0.2286, 'swir2': 0.1596},
                        'ls8': {'blue': 0.3029, 'green': 0.2786, 'red': 0.4733,
                                'nir': 0.5599, 'swir1': 0.508, 'swir2': 0.1872}}

    # Dict to use correct coefficients for each tasseled cap band
    analysis_coefficient = {'wetness': wetness_coeff,
                            'greenness': greenness_coeff,
                            'brightness': brightness_coeff}

    # For each band, compute tasseled cap band and add to output dataset
    for tc_band in tc_bands:
        # Create xarray of coefficient values used to multiply each band of input
        coeff = xr.Dataset(analysis_coefficient[tc_band][sensor])
        sensor_coeff = sensor_data * coeff

        # Sum all bands
        output_array[tc_band] = sensor_coeff.blue + sensor_coeff.green + \
                                sensor_coeff.red + sensor_coeff.nir + \
                                sensor_coeff.swir1 + sensor_coeff.swir2

    # If drop = True, remove original bands
    if drop:
        bands_to_drop = list(sensor_data.data_vars)
        output_array = output_array.drop(bands_to_drop)

    return output_array


def dataset_to_geotiff(filename, data):

    '''
    this function uses rasterio and numpy to write a multi-band geotiff for one
    timeslice, or for a single composite image. It assumes the input data is an
    xarray dataset (note, dataset not dataarray) and that you have crs and affine
    objects attached, and that you are using float data. future users
    may wish to assert that these assumptions are correct.

    Last modified: March 2018
    Authors: Bex Dunn and Josh Sixsmith
    Modified by: Claire Krause, Robbi Bishop-Taylor

    inputs
    filename - string containing filename to write out to
    data - dataset to write out
    Note: this function currently requires the data have lat/lon only, i.e. no
    time dimension
    '''

    # Depreciation warning for write_geotiff
    print("This function will be superceded by the 'write_geotiff' function from 'datacube.helpers'. "
          "Please revise your notebooks to use this function instead")

    kwargs = {'driver': 'GTiff',
              'count': len(data.data_vars),  # geomedian no time dim
              'width': data.sizes['x'], 'height': data.sizes['y'],
              'crs': data.crs.crs_str,
              'transform': data.affine,
              'dtype': list(data.data_vars.values())[0].values.dtype,
              'nodata': 0,
              'compress': 'deflate', 'zlevel': 4, 'predictor': 3}
    # for ints use 2 for floats use 3}

    with rasterio.open(filename, 'w', **kwargs) as src:
        for i, band in enumerate(data.data_vars):
            src.write(data[band].data, i + 1)
            
def open_polygon_from_shapefile(shapefile, index_of_polygon_within_shapefile=0):

    '''This function takes a shapefile, selects a polygon as per your selection, 
    uses the datacube geometry object, along with shapely.geometry and fiona to 
    get the geom for the datacube query. It will also make sure you have the correct 
    crs object for the DEA

    Last modified May 2018
    Author: Bex Dunn'''

    # open all the shapes within the shape file
    shapes = fiona.open(shapefile)
    i =index_of_polygon_within_shapefile
    #print('shapefile index is '+str(i))
    if i > len(shapes):
        print('index not in the range for the shapefile'+str(i)+' not in '+str(len(shapes)))
        sys.exit(0)
    #copy attributes from shapefile and define shape_name
    geom_crs = geometry.CRS(shapes.crs_wkt)
    geo = shapes[i]['geometry']
    geom = geometry.Geometry(geo, crs=geom_crs)
    geom_bs = shapely.geometry.shape(shapes[i]['geometry'])
    shape_name = shapefile.split('/')[-1].split('.')[0]+'_'+str(i)
    #print('the name of your shape is '+shape_name)
    #get your polygon out as a geom to go into the query, and the shape name for file names later
    return geom, shape_name          

def write_your_netcdf(data, dataset_name, filename, crs):

    '''this function turns an xarray dataarray into a dataset so we can write it to netcdf. 
    It adds on a crs definition from the original array. data = your xarray dataset, dataset_name 
    is a string describing your variable''' 
   
    #turn array into dataset so we can write the netcdf
    if isinstance(data,xr.DataArray):
        dataset= data.to_dataset(name=dataset_name)
    elif isinstance(data,xr.Dataset):
        dataset = data
    else:
        print('your data might be the wrong type, it is: '+type(data))
    #grab our crs attributes to write a spatially-referenced netcdf
    dataset.attrs['crs'] = crs

    try:
        write_dataset_to_netcdf(dataset, filename)
    except RuntimeError as err:
        print("RuntimeError: {0}".format(err))    


# def zonal_timeseries(dataArray, shp_loc, results_loc, feature_name, stat='mean', csv=False, netcdf=False, plot=False):
#     """
#     Summary: 
#     Given an xarray dataArray and a shapefile, generates a timeseries of zonal statistics across n number of 
#     uniquely labelled polygons. The function exports a .csv of the stats, a netcdf containing the stats, and .pdf plots.
#     Requires the installation of the rasterstats module: https://pythonhosted.org/rasterstats/installation.html
    
#     Inputs:
#     data = xarray dataarray (note dataarray, not dataset - it is a requirement the data only have a single variable).
#     shp_loc = string. Location of the shapefile used to extract the zonal timseries.
#     results_loc = string. Location of the directory where results should export.
#     feature_name = string. Name of attribute column in the shapefile that is of interest - used to label dataframe, plots etc.
#     stat = string.  The statistic you want to extract. Options include 'count', 'max', 'median', 'min', 'std'.
#     plot = Boolean. If True, function will produce pdfs of timeseries for each polygon in the shapefile.
#     csv = Boolean. If True, function will export results as a .csv.
#     netcdf = Boolean. If True, function will export results as a netcdf.
    
#     Last modified: May 2018
#     Author: Chad Burton
    
#     """
#     #use dask to chunk the data along the time axis in case its a very large dataset
#     dataArray = dataArray.chunk(chunks = {'time':20})
    
#     #create 'transform' tuple to provide ndarray with geo-referencing data. 
#     one = float(dataArray.x[0])
#     two = float(dataArray.y[0] - dataArray.y[1])
#     three = 0.0
#     four = float(dataArray.y[0])
#     five = 0.0
#     six = float(dataArray.x[0] - dataArray.x[1])

#     transform_zonal = (one, two, three, four, five, six)

#     #import shapefile, make sure its in the right projection to match the dataArray
#     #and set index to the feature_name
#     project_area = gpd.read_file(shp_loc)               #get the shapefile
#     reproj=int(str(dataArray.crs)[5:])                  #do a little hack to get EPSG from the dataArray 
#     project_area = project_area.to_crs(epsg=reproj)     #reproject shapefile to match dataArray
#     project_area = project_area.set_index(feature_name) #set the index
    
#     #define the general function
#     def zonalStats(dataArray, stat=stat): 
#         """extract the zonal statistics of all
#         pixel values within each polygon"""
#         stats = [] 
#         for i in dataArray:
#             x = rs.zonal_stats(project_area, i, transform=transform_zonal, stats=stat)    
#             stats.append(x)
#         #extract just the values from the results, and convert 'None' values to nan
#         stats = [[t[stat] if t[stat] is not None else np.nan for t in feature] for feature in stats]
#         stats = np.array(stats)
#         return stats

#     #use the zonal_stats functions to extract the stats:
#     n = len(project_area) #number of polygons in the shapefile (defines the dimesions of the output)
#     statistics = dataArray.data.map_blocks(zonalStats, chunks=(-1,n), drop_axis=1, dtype=np.float64).compute()

#     #get unique identifier and timeseries data from the inputs 
#     colnames = pd.Series(project_area.index.values)
#     time = pd.Series(dataArray['time'].values)

#     #define functions for cleaning up the results of the rasterstats operation
#     def tidyresults(results):
#         x = pd.DataFrame(results).T #transpose
#         x = x.rename(colnames, axis='index') #rename the columns to the timestamp
#         x = x.rename(columns = time)
#         return x

#     #place results into indexed dataframes using tidyresults function
#     statistics_df = tidyresults(statistics)
    
#     #convert into xarray for merging into a dataset
#     stat_xr = xr.DataArray(statistics_df, dims=[feature_name, 'time'], coords={feature_name: statistics_df.index, 'time': time}, name= stat)
    
#     #options for exporting results as csv, netcdf, pdf plots
#     #export results as a .csv
#     if csv:
#         statistics_df.to_csv('{0}{1}.csv'.format(results_loc, stat))
                             
#     if netcdf:
#         #export out results as netcdf
#         stat_xr.to_netcdf('{0}zonalstats_{1}.nc'.format(results_loc, stat), mode='w',format='NETCDF4') 

#     if plot:     
#         #place the data from the xarray into a list
#         plot_data = []
#         for i in range(0,len(stat_xr[feature_name])):
#             x = stat_xr.isel([stat], **{feature_name: i})
#             plot_data.append(x)

#         #extract the unique names of each polygon
#         feature_names = list(stat_xr[feature_name].values)

#         #zip the both the data and names together as a dictionary 
#         monthly_dict = dict(zip(feature_names,plot_data))

#         #create a function for generating the plots
#         def plotResults(dataArray, title):
#             """a function for plotting up the results of the
#             fractional cover change and exporting it out as pdf """
#             x = dataArray.time.values
#             y = dataArray.data          

#             plt.figure(figsize=(15,5))
#             plt.plot(x, y,'k', color='#228b22', linewidth = 1)
#             plt.grid(True, linestyle ='--')
#             plt.title(title)
#             plt.savefig('{0}{1}.pdf'.format(results_loc, title), bbox_inches='tight')

#         #loop over the dictionaries and create the plots
#         {key: plotResults(monthly_dict[key], key + "_"+ stat) for key in monthly_dict} 
    
#     #return the results as a dataframe
#     return statistics_df
