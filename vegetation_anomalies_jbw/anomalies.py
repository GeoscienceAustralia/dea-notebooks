import numpy as np
import xarray as xr
import fiona
import math
import rasterio.features
import datacube 
import warnings
from datacube.storage import masking
from datacube.utils import geometry
from datacube.helpers import ga_pq_fuser
from dea_datahandling import load_ard
import folium
from pyproj import Proj, transform
import os
import gdal
import zipfile
import numexpr
import datetime
import requests
import warnings
import odc.algo


def _dc_query_only(**kw):
    """
    Remove load-only parameters, the rest can be passed to Query
    Returns
    -------
    dict of query parameters
    """

    def _impl(measurements=None,
              output_crs=None,
              resolution=None,
              resampling=None,
              skip_broken_datasets=None,
              dask_chunks=None,
              fuse_func=None,
              align=None,
              datasets=None,
              progress_cbk=None,
              group_by=None,
              **query):
        return query

    return _impl(**kw)


def _common_bands(dc, products):
    """
    Takes a list of products and returns a list of measurements/bands
    that are present in all products
    Returns
    -------
    List of band names
    """
    common = None
    bands = None

    for p in products:
        p = dc.index.products.get_by_name(p)
        if common is None:
            common = set(p.measurements)
            bands = list(p.measurements)
        else:
            common = common.intersection(set(p.measurements))
    return [band for band in bands if band in common]


# def load_ard(dc,
#              products=None,
#              min_gooddata=0.0,
#              fmask_categories=['valid', 'snow', 'water'],
#              mask_pixel_quality=True,
#              mask_contiguity=False,
#              ls7_slc_off=True,
#              predicate=None,
#              dtype='auto',
#              **kwargs):


#     #########
#     # Setup #
#     #########

#     # Use 'nbart_contiguity' by default if mask_contiguity is true
#     if mask_contiguity is True:
#         mask_contiguity = 'nbart_contiguity'

#     # We deal with `dask_chunks` separately
#     dask_chunks = kwargs.pop('dask_chunks', None)
#     requested_measurements = kwargs.pop('measurements', None)

#     # Warn user if they combine lazy load with min_gooddata
#     if (min_gooddata > 0.0) and dask_chunks is not None:
#         warnings.warn("Setting 'min_gooddata' percentage to > 0.0 "
#                       "will cause dask arrays to compute when "
#                       "loading pixel-quality data to calculate "
#                       "'good pixel' percentage. This can "
#                       "slow the return of your dataset.")

#     # Verify that products were provided, and determine if Sentinel-2
#     # or Landsat data is being loaded
#     if not products:
#         raise ValueError("Please provide a list of product names "
#                          "to load data from. Valid options are: \n"
#                          "['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'] "
#                          "for Landsat, ['s2a_ard_granule', "
#                          "'s2b_ard_granule'] \nfor Sentinel 2 Definitive, or "
#                          "['s2a_nrt_granule', 's2b_nrt_granule'] for "
#                          "Sentinel 2 Near Real Time")
#     elif all(['ls' in product for product in products]):
#         product_type = 'ls'
#     elif all(['s2' in product for product in products]):
#         product_type = 's2'

#     fmask_band = 'fmask'
#     measurements = requested_measurements.copy() if requested_measurements else None

#     if measurements is None:
        
#         # Deal with "load all" case: pick a set of bands common across 
#         # all products
#         measurements = _common_bands(dc, products)

#         # If no `measurements` are specified, Landsat ancillary bands are 
#         # loaded with a 'oa_' prefix, but Sentinel-2 bands are not. As a 
#         # work-around, we need to rename the default contiguity and fmask 
#         # bands if loading Landsat data without specifying `measurements`
#         if product_type == 'ls':
#             mask_contiguity = f'oa_{mask_contiguity}' if mask_contiguity else False
#             fmask_band = f'oa_{fmask_band}'

#     # If `measurements` are specified but do not include fmask or
#     # contiguity variables, add these to `measurements`
#     if fmask_band not in measurements:
#         measurements.append(fmask_band)
#     if mask_contiguity and mask_contiguity not in measurements:
#         measurements.append(mask_contiguity)

#     # Get list of data and mask bands so that we can later exclude
#     # mask bands from being masked themselves
#     data_bands = [band for band in measurements if band not in (fmask_band, mask_contiguity)]
#     mask_bands = [band for band in measurements if band not in data_bands]

#     #################
#     # Find datasets #
#     #################

#     # Pull out query params only to pass to dc.find_datasets
#     query = _dc_query_only(**kwargs)
    
#     # Extract datasets for each product using subset of dcload_kwargs
#     dataset_list = []

#     # Get list of datasets for each product
#     print('Finding datasets')
#     for product in products:

#         # Obtain list of datasets for product
#         print(f'    {product} (ignoring SLC-off observations)' 
#               if not ls7_slc_off and product == 'ga_ls7e_ard_3' 
#               else f'    {product}')
#         datasets = dc.find_datasets(product=product, **query)

# #         # Remove Landsat 7 SLC-off observations if ls7_slc_off=False
# #         if not ls7_slc_off and product == 'ga_ls7e_ard_3':
# #             datasets = [i for i in datasets if i.time.begin <
# #                         datetime.datetime(2003, 5, 31)]

# #              # Remove Landsat 7 SLC-off observations if ls7_slc_off=False %from dea_handling
# #         if not ls7_slc_off and product == 'ga_ls7e_ard_3':
# #             datasets = [i for i in datasets if
# #                         normalise_dt(i.time.begin) <
# #                         datetime.datetime(2003, 5, 31)]
                

#         # Add any returned datasets to list
#         dataset_list.extend(datasets)

#     # Raise exception if no datasets are returned
#     if len(dataset_list) == 0:
#         raise ValueError("No data available for query: ensure that "
#                          "the products specified have data for the "
#                          "time and location requested")

#     # If predicate is specified, use this function to filter the list
#     # of datasets prior to load
#     if predicate:
#         print(f'Filtering datasets using predicate function')
#         dataset_list = [ds for ds in dataset_list if predicate(ds)]

#     # Raise exception if filtering removes all datasets
#     if len(dataset_list) == 0:
#         raise ValueError("No data available after filtering with "
#                          "predicate function")

#     #############
#     # Load data #
#     #############

#     # Note we always load using dask here so that we can lazy load data 
#     # before filtering by good data
#     ds = dc.load(datasets=dataset_list,
#                  measurements=measurements,
#                  dask_chunks={} if dask_chunks is None else dask_chunks,
#                  **kwargs)

#     ####################
#     # Filter good data #
#     ####################

#     # Calculate pixel quality mask
#     pq_mask = odc.algo.fmask_to_bool(ds[fmask_band],
#                                      categories=fmask_categories)

#     # The good data percentage calculation has to load in all `fmask`
#     # data, which can be slow. If the user has chosen no filtering
#     # by using the default `min_gooddata = 0`, we can skip this step
#     # completely to save processing time
#     if min_gooddata > 0.0:

#         # Compute good data for each observation as % of total pixels
#         print('Counting good quality pixels for each time step')
#         data_perc = (pq_mask.sum(axis=[1, 2], dtype='int32') /
#                      (pq_mask.shape[1] * pq_mask.shape[2]))
#         keep = data_perc >= min_gooddata

#         # Filter by `min_gooddata` to drop low quality observations
#         total_obs = len(ds.time)
#         ds = ds.sel(time=keep)
#         pq_mask = pq_mask.sel(time=keep)

#         print(f'Filtering to {len(ds.time)} out of {total_obs} '
#               f'time steps with at least {min_gooddata:.1%} '
#               f'good quality pixels')
        
#     ###############
#     # Apply masks #
#     ###############      
    
#     # Create an overall mask to hold both pixel quality and contiguity
#     mask = None    
    
#     # Add pixel quality mask to overall mask
#     if mask_pixel_quality:
#         print('Applying pixel quality/cloud mask')
#         mask = pq_mask

#     # Add contiguity mask to overall mask
#     if mask_contiguity:
#         print('Applying contiguity mask')
#         cont_mask = ds[mask_contiguity] == 1

#         # If mask already has data if mask_pixel_quality == True,
#         # multiply with cont_mask to perform a logical 'or' operation
#         # (keeping only pixels good in both)
#         mask = cont_mask if mask is None else mask * cont_mask

#     # Split into data/masks bands, as conversion to float and masking 
#     # should only be applied to data bands
#     ds_data = ds[data_bands]
#     ds_masks = ds[mask_bands]

#     # Mask data if either of the above masks were generated
#     if mask is not None:
#         ds_data = odc.algo.keep_good_only(ds_data, where=mask)

#     # Automatically set dtype to either native or float32 depending
#     # on whether masking was requested
#     if dtype == 'auto':
#         dtype = 'native' if mask is None else 'float32'
    
#     # Set nodata values using odc.algo tools to reduce peak memory
#     # use when converting data dtype    
#     if dtype != 'native':
#         ds_data = odc.algo.to_float(ds_data, dtype=dtype)

#     # Put data and mask bands back together
#     attrs = ds.attrs
#     ds = xr.merge([ds_data, ds_masks])
#     ds.attrs.update(attrs)
    
#     ###############
#     # Return data #
#     ###############

#     # Drop bands not originally requested by user
#     if requested_measurements:
#         ds = ds[requested_measurements]

#     # If user supplied dask_chunks, return data as a dask array without
#     # actually loading it in
#     if dask_chunks is not None:
#         print(f'Returning {len(ds.time)} time steps as a dask array')
#         return ds
#     else:
#         print(f'Loading {len(ds.time)} time steps')
#         return ds.compute()
    

def calculate_anomalies(shp_fpath,
                        collection,
                        year,
                        season,
                        query_box,
                        dask_chunks):
    
    # dict of all seasons for indexing datacube
    all_seasons = {'JFM': [1,2,3],
                   'FMA': [2,3,4],
                   'MAM': [3,4,5],
                   'AMJ': [4,5,6],
                   'MJJ': [5,6,7],
                   'JJA': [6,7,8],
                   'JAS': [7,8,9],
                   'ASO': [8,9,10],
                   'SON': [9,10,11],
                   'OND': [10,11,12],
                   'NDJ': [11,12,1],
                   'DJF': [12,1,2],
                  }

    if season not in all_seasons:
        raise ValueError("Not a valid season, "
                         "must be one of: " + str(all_seasons.keys()))
         
    #Depending on the season, grab the time for the dc.load
    months=all_seasons.get(season)
        
    if (season == 'DJF') or (season == 'NDJ'):
        time= (year+"-"+str(months[0]), str(int(year)+1)+"-"+str(months[2]))
    
    else:
        time = (year+"-"+str(months[0]), year+"-"+str(months[2]))
   
    #connect to datacube
    try:
        if collection == 'c3':
#             dc = datacube.Datacube(app='calculate_anomalies', env='c3-samples')
            dc = datacube.Datacube(app='calculate_anomalies') #jbw
        if collection == 'c2':
            dc = datacube.Datacube(app='calculate_anomalies')
    except:
        raise ValueError("collection must be either 'c3' or 'c2'")
    
    #get data from shapefile extent and mask
    if shp_fpath is not None:
        
        if len(fiona.open(shp_fpath)) > 1:
            warnings.warn("This script can only accept shapefiles with a single polygon feature; "
                          "seasonal anomalies will be calculated for the extent of the "
                          "first geometry in the shapefile only.")
        
        print("extracting data based on shapefile extent")
        
        with fiona.open(shp_fpath) as input:
            crs = geometry.CRS(input.crs_wkt)
        
        feat = fiona.open(shp_fpath)[0]
        first_geom = feat['geometry']
        geom = geometry.Geometry(first_geom, crs=crs)

        query = {'geopolygon': geom,
                 'time': time}
        
        if collection == 'c3': 
        
            ds = load_ard(dc=dc,
                      products = ['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'],
                      measurements = ['nbart_nir', 'nbart_red'],
                      ls7_slc_off = False,
                      #align = (15,15),
                      resolution=(-30,30),
                      output_crs = 'epsg:3577',
                      dask_chunks = dask_chunks,
                      group_by='solar_day',
                      **query)
        
        if collection == 'c2':
            print('loading Landsat C2')
            ds = dc.load(product=['ls8_nbart_albers','ls7_nbart_albers'],
                           group_by='solar_day',
                           measurements = ['nir', 'red'],
                           resolution=(-30,30),
                           output_crs = 'epsg:3577',
                           dask_chunks=dask_chunks,
                           **query)             
            
            # Load PQ data
            print('loading Landsat C2 pq data')
            pq = dc.load(product=['ls8_pq_albers','ls7_pq_albers'],
                         group_by='solar_day',
                         fuse_func=ga_pq_fuser,
                         resolution=(-30,30),
                         output_crs = 'epsg:3577',  
                         dask_chunks=dask_chunks,
                         **query)        
            
            print('making pq mask')
            good_quality = masking.make_mask(pq.pixelquality,                         
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
            
            attrs = ds.attrs
            ds = ds.astype(np.float32)
            ds = ds.where(good_quality)
            ds = masking.mask_invalid_data(ds)
            ds.attrs.update(attrs)

        
        mask = rasterio.features.geometry_mask([geom.to_crs(ds.geobox.crs)for geoms in [geom]],
                                       out_shape=ds.geobox.shape,
                                       transform=ds.geobox.affine,
                                       all_touched=False,
                                       invert=False)
        
        mask_xr = xr.DataArray(mask, dims = ('y','x'))
        ds = ds.where(mask_xr==False)
        
        
    else: 
        print('Extracting data based on lat, lon coords')
        query = {'lon': (query_box[1] - query_box[2], query_box[1] + query_box[2]),
                 'lat': (query_box[0] - query_box[2], query_box[0] + query_box[2]),
                 'time': time}
            
        if collection=='c3':
            
            ds = load_ard(dc=dc,
                          products =['ga_ls5t_ard_3', 'ga_ls7e_ard_3', 'ga_ls8c_ard_3'],
                          measurements = ['nbart_nir', 'nbart_red'],
                          ls7_slc_off = False,
                          #align = (15,15),
                          resolution=(-30,30),
                          output_crs = 'epsg:3577',
                          dask_chunks = dask_chunks,
                          group_by='solar_day',
                          **query)
            
        if collection=='c2':
            
            print('loading Landsat collection 2')
            ds = dc.load(product=['ls8_nbart_albers','ls7_nbart_albers'],
                           group_by='solar_day',
                           measurements = ['nir', 'red'],
                           resolution=(-30,30),
                           output_crs = 'epsg:3577',
                           dask_chunks=dask_chunks,
                           **query)             

            # Load PQ data
            pq = dc.load(product=['ls8_pq_albers','ls7_pq_albers'],
                         group_by='solar_day',
                         fuse_func=ga_pq_fuser,
                         resolution=(-30,30),
                         output_crs = 'epsg:3577',  
                         dask_chunks=dask_chunks,
                         **query)         


            good_quality = masking.make_mask(pq.pixelquality,                         
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

            attrs = ds.attrs
            ds = ds.astype(np.float32)
            ds = ds.where(good_quality)
            ds = masking.mask_invalid_data(ds)
            ds.attrs.update(attrs)

            
    print("start: "+str(ds.time.values[0])+", end: "+str(ds.time.values[-1])+", time dim length: "+str(len(ds.time.values)))
    print('calculating vegetation indice')
    if collection=='c3':
        vegIndex = (ds.nbart_nir - ds.nbart_red) / (ds.nbart_nir + ds.nbart_red)
    if collection=='c2':
        vegIndex = (ds.nir - ds.red) / (ds.nir + ds.red)
    
    vegIndex = vegIndex.mean('time').rename('ndvi_mean')
        
    #get the bounding coords of the input ds to help with indexing the climatology
    xmin, xmax = vegIndex.x.values[0], vegIndex.x.values[-1]
    ymin,ymax = vegIndex.y.values[0], vegIndex.y.values[-1]
    x_slice = [i for i in range(int(xmin),int(xmax+30),30)]
    y_slice = [i for i in range(int(ymin),int(ymax-30),-30)]
    
    #index the climatology dataset to the location of our AOI
    climatology_mean = xr.open_rasterio('results/NSW_NDVI_Climatologies_mean/mosaics/ndvi_clim_mean_'+season+'_nsw.tif').sel(x=x_slice,
                                                                y=y_slice,
                                                                method='nearest').chunk(chunks=dask_chunks).squeeze()
    
    climatology_std = xr.open_rasterio('results/NSW_NDVI_Climatologies_std/mosaics/ndvi_clim_std_'+season+'_nsw.tif').sel(x=x_slice,
                                                                y=y_slice,
                                                                method='nearest').chunk(chunks=dask_chunks).squeeze()
    
    #test if the arrays match before we calculate the anomalies
    np.testing.assert_allclose(vegIndex.x.values, climatology_mean.x.values,
                              err_msg="The X coordinates on the AOI dataset do not match "
                                      "the X coordinates on the climatology mean dataset. "
                                       "You're AOI may be beyond the extent of the pre-computed "
                                       "climatology dataset.")
    
    np.testing.assert_allclose(vegIndex.y.values, climatology_mean.y.values,
                          err_msg="The Y coordinates on the AOI dataset do not match "
                                  "the Y coordinates on the climatology mean dataset. "
                                   "You're AOI may be beyond the extent of the pre-computed "
                                   "climatology dataset.")
    
    np.testing.assert_allclose(vegIndex.x.values, climatology_std.x.values,
                              err_msg="The X coordinates on the AOI dataset do not match "
                                      "the X coordinates on the climatology std dev dataset. "
                                       "You're AOI may be beyond the extent of the pre-computed "
                                       "climatology dataset.")
    
    np.testing.assert_allclose(vegIndex.y.values, climatology_std.y.values,
                          err_msg="The Y coordinates on the AOI dataset do not match "
                                  "the Y coordinates on the climatology std dev dataset. "
                                   "You're AOI may be beyond the extent of the pre-computed "
                                   "climatology dataset.")
    
    print('calculating anomalies')
    #calculate standardised anomalies
    anomalies = xr.apply_ufunc(lambda x, m, s: (x - m) / s,
                               vegIndex, climatology_mean, climatology_std,
                               output_dtypes=[np.float32],
                               dask='parallelized')
    
    #add back metadata
    anomalies = anomalies.rename('std_anomalies').to_dataset()
    anomalies.attrs = ds.attrs
    anomalies.attrs['units'] = 1
    
    obs=ds.time

    return anomalies,obs


