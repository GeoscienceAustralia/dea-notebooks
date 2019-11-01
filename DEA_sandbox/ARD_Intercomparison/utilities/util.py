# -*- coding: utf-8 -*-
"""
Created on Wed May 22 09:45:47 2019

@author: u89076
"""

from pyproj import Proj, transform
import rasterio
import rasterio.features
import numpy as np
from datacube.storage import masking
import warnings
from datacube import Datacube
import xarray as xr
import logging as log
from datetime import datetime
import plotly
import fiona
from datacube.utils import geometry
import os
import csv
from os.path import join as pjoin
import configparser
import ast


# functions to retrieve data

def setQueryExtent(target_epsg, lon_cen, lat_cen, size_m):
    """
    Set the query extent in meteres as per the central geographical coordinates
    and the extent in meters.
    
    """
    
    inProj = Proj(init='epsg:4326')
    outProj = Proj(init=target_epsg)    
    x_cen,y_cen = transform(inProj, outProj, lon_cen, lat_cen)
     
    x1 = x_cen - size_m /2 
    x2 = x_cen + size_m /2 
    y1 = y_cen + size_m /2 
    y2 = y_cen - size_m /2 
    
    return x1, y1, x2, y2    
    
    
def geometry_mask(geoms, geobox, all_touched=False, invert=False):
    """
    Create a mask from shapes.

    By default, mask is intended for use as a
    numpy mask, where pixels that overlap shapes are False.
    :param list[Geometry] geoms: geometries to be rasterized
    :param datacube.utils.GeoBox geobox:
    :param bool all_touched: If True, all pixels touched by geometries will be
                             burned in. If false, only pixels whose center is 
                             within the polygon or that are selected by 
                             Bresenham's line algorithm will be burned in.
    :param bool invert: If True, mask will be True for pixels that overlap 
                        shapes.
    """
    
    return rasterio.features.geometry_mask([geom.to_crs(geobox.crs) for geom in geoms],
                                           out_shape=geobox.shape,
                                           transform=geobox.affine,
                                           all_touched=all_touched,
                                           invert=invert)
                                           
                                           
def get_pixel_size(dataset, source_band_list):
    """
    Decide the pixel size for loading the dataset from datacube
    """
    
    image_meta = dataset.metadata_doc['image']
    pixel_x_list = []
    pixel_y_list = []
    for a_band in source_band_list:
        if 'bands_info' in image_meta:
            # usgs level2
            pixel_x_list.append(int(image_meta['bands_info'][a_band]['pixel_size']['x']))
            pixel_y_list.append(abs(int(image_meta['bands_info'][a_band]['pixel_size']['y'])))
        else: 
            pixel_x_list.append(int(image_meta['bands'][a_band]['info']['geotransform'][1]))
            pixel_y_list.append(abs(int(image_meta['bands'][a_band]['info']['geotransform'][5])))

    pixel_x = min(pixel_x_list)
    pixel_y = min(pixel_y_list)
    
    return pixel_x, pixel_y  


def get_epsg(dataset):
    sr = dataset.metadata.grid_spatial['spatial_reference']
    if 'PROJCS' in sr:
        start_loc = sr.rfind('EPSG')
        epsg = '{}:{}'.format(sr[start_loc:start_loc+4], sr[start_loc+7:-3])
    else:
        # lansat ard
        epsg = sr
        
    return epsg


def remove_cloud_nodata(source_prod, data, mask_band): 
    ls8_USGS_cloud_pixel_qa_value = [324, 352, 368, 386, 388, 392, 400, 416, 
                                     432, 480, 864, 880, 898, 900, 904, 928, 
                                     944, 992, 1350]
    non_ls8_USGS_cloud_pixel_qa_value = [72, 96, 112, 130, 132, 136, 144, 160, 
                                         176, 224]
    non_ls8_USGS_sr_cloud_qa_value = [2, 4, 12, 20, 34, 36, 52]
    mask_data = data[mask_band]
    nodata_value = mask_data.nodata
    nodata_cloud_value = []
    
    if 'usgs' in source_prod:
        if 'ls8' in source_prod:
            nodata_cloud_value = ls8_USGS_cloud_pixel_qa_value
        else:
            if mask_band == 'sr_cloud_qa':
                nodata_cloud_value = non_ls8_USGS_sr_cloud_qa_value
            else:
                nodata_cloud_value = non_ls8_USGS_cloud_pixel_qa_value
                
        nodata_cloud_value.append(nodata_value)
        nodata_cloud = np.isin(mask_data, nodata_cloud_value) 
        cld_free = data.where(~nodata_cloud).dropna(dim='time', how='all')
    else:
        cld_free = data.where(mask_data == 1).dropna(dim='time', how='all')
           
    # remove nodata for the pixel of interest
    cld_free_valid = masking.mask_invalid_data(cld_free)
    
    return cld_free_valid

    
def only_return_whole_scene(data):
    
    all_time_list = list(data.time.values)
    partial_time_list = []
    
    for band in data.data_vars:
        band_info = data[band]
        for a_time in all_time_list:
            valid_pixel_no = np.count_nonzero(~np.isnan(band_info.loc[a_time].values)) 
            # partial scenes
            if valid_pixel_no < band_info.loc[a_time].values.size:
                partial_time_list.append(a_time)
                break
    
    valid_time_list = list(set(all_time_list) - set(partial_time_list))
    valid_data = data.sel(time=valid_time_list).sortby('time')
    
    return valid_data
    
    
def round_time_ns(input_data):
    data = input_data
    for i in range(len(data.time)):
        data.time.values[i] = str(data.time.values[i])[:16]
    return data
    

def back2original_time_ns(data, orig_time):
    for i in range(len(data.time)):
        for a_time in orig_time:
            if str(data.time.values[i])[:16] in str(a_time):
                data.time.values[i] = a_time
                break            
    return data

    
def get_common_dates_data(items_list):
    # round time so to igonor difference on seconds
    original_time_list = []
    data_round_list = []
    for item in items_list:
        data_only = item[list(item.keys())[0]]['data']
        original_time_list.append(list(data_only.time.values))
        data_round_list.append(round_time_ns(data_only))

    # find common dates
    common_dates = set(data_round_list[0].time.values)
    for a_data in data_round_list[1:]:
        common_dates.intersection_update(set(a_data.time.values))
    
    # find the data with common dates and convert back to original time
    i = 0
    for a_data in data_round_list:
        data_common = a_data.sel(time=list(common_dates), method='nearest').sortby('time')
        data_common = back2original_time_ns(data_common, original_time_list[i])       
        # replace the old data with the common_original_data
        items_list[i][list(items_list[i].keys())[0]]['data'] = data_common
        i+=1
                
    return items_list
    

def get_common_dates(input_data_list):
    for key, items_list in input_data_list.items():
        if len(items_list) > 1:
            common_dates_item_list = get_common_dates_data(items_list)
        else:
            common_dates_item_list = []
            
        input_data_list[key] = common_dates_item_list
    return input_data_list   
    
    
def get_data_opensource(prod_info, input_lon, input_lat, acq_min, acq_max, 
                        window_size, no_partial_scenes): 
    
    datacube_config = prod_info[0]
    source_prod = prod_info[1]
    source_band_list = prod_info[2]
    mask_band = prod_info[3]
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if datacube_config != 'default':
            remotedc = Datacube(config=datacube_config)
        else:
            remotedc = Datacube()

        return_data = {}
        data = xr.Dataset()

        if source_prod != '':
            # find dataset to get metadata
            fd_query = {        
                'time': (acq_min, acq_max),
                 'x' : (input_lon, input_lon+window_size/100000),
                 'y' : (input_lat, input_lat+window_size/100000),
                }
            sample_fd_ds = remotedc.find_datasets(product=source_prod, 
                                                  group_by='solar_day', 
                                                  **fd_query)                      

            if (len(sample_fd_ds)) > 0:
                # decidce pixel size for output data
                pixel_x, pixel_y = get_pixel_size(sample_fd_ds[0], 
                                                  source_band_list)
                
                log.info('Output pixel size for product {}: x={}, y={}'.format(source_prod, pixel_x, pixel_y))

                # get target epsg from metadata
                target_epsg = get_epsg(sample_fd_ds[0])
                log.info('CRS for product {}: {}'.format(source_prod, 
                                                         target_epsg))

                x1, y1, x2, y2 = setQueryExtent(target_epsg, input_lon, 
                                                input_lat, window_size)                                                              
                
                query = {        
                    'time': (acq_min, acq_max),
                     'x' : (x1, x2),
                     'y' : (y1, y2),
                     'crs' : target_epsg,
                     'output_crs' : target_epsg,
                     'resolution': (-pixel_y, pixel_x),  
                     'measurements': source_band_list   
                    }

                if 's2' in source_prod:
                    data = remotedc.load(product=source_prod, 
                                         group_by='solar_day', **query)
                else:
                    data = remotedc.load(product=source_prod, 
                                         align=(pixel_x/2.0, pixel_y/2.0), 
                                         group_by='solar_day', **query)
                # remove cloud and nodta    
                data = remove_cloud_nodata(source_prod, data, mask_band)
                
                if no_partial_scenes:
                    # calculate valid data percentage
                    data = only_return_whole_scene(data)

            return_data = { 
                           source_prod: {'data': data, 
                                         'mask_band': mask_band,
                                         'find_list': sample_fd_ds }
                          }
    
    return return_data 
    
    
# loading data by a shapefile
def get_data_opensource_shapefile(prod_info, acq_min, acq_max, shapefile, 
                                  no_partial_scenes):
    
    datacube_config = prod_info[0]
    source_prod = prod_info[1]
    source_band_list = prod_info[2]
    mask_band = prod_info[3]    
    
    if datacube_config != 'default':
        remotedc = Datacube(config=datacube_config)
    else:
        remotedc = Datacube()
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with fiona.open(shapefile) as shapes:
            crs = geometry.CRS(shapes.crs_wkt)
            first_geometry = next(iter(shapes))['geometry']
            geom = geometry.Geometry(first_geometry, crs=crs)            

            return_data = {} 
            data = xr.Dataset()
            
            if source_prod != '': 
                # get a sample dataset to decide the target epsg
                fd_query = {        
                    'time': (acq_min, acq_max),
                     'geopolygon': geom
                    }
                sample_fd_ds = remotedc.find_datasets(product=source_prod, 
                                                      group_by='solar_day',
                                                      **fd_query)

                if (len(sample_fd_ds)) > 0:
                    # decidce pixel size for output data
                    pixel_x, pixel_y = get_pixel_size(sample_fd_ds[0], 
                                                      source_band_list)
                    log.info('Output pixel size for product {}: x={}, y={}'.format(source_prod, pixel_x, pixel_y))

                    # get target epsg from metadata
                    target_epsg = get_epsg(sample_fd_ds[0])
                    log.info('CRS for product {}: {}'.format(source_prod, 
                                                             target_epsg))
                        
                    query = {
                            'time': (acq_min, acq_max),
                            'geopolygon': geom,
                            'output_crs' : target_epsg,
                            'resolution': (-pixel_y, pixel_x),
                            'measurements': source_band_list
                            }

                    if 's2' in source_prod:
                        data = remotedc.load(product=source_prod, 
                                             group_by='solar_day', **query)
                    else:
                        data = remotedc.load(product=source_prod, 
                                             align=(pixel_x/2.0, pixel_y/2.0), 
                                             group_by='solar_day', **query)
                    
                    # remove cloud and nodta    
                    data = remove_cloud_nodata(source_prod, data, mask_band) 
                    
                    if data.data_vars: 
                        mask = geometry_mask([geom], data.geobox, invert=True) 
                        data = data.where(mask)

                    if no_partial_scenes:
                        # calculate valid data percentage
                        data = only_return_whole_scene(data)                                             

                return_data = {
                               source_prod: {'data': data,
                                             'mask_band': mask_band,
                                             'find_list': sample_fd_ds }
                              }
                    
    return return_data 


def aleady_loaded(a_prod, acq_min, acq_max, data_list, **kwargs):    
    loc_time = (kwargs['loc'], (acq_min, acq_max))        
    loaded = False    
    if loc_time in data_list:
        # find all products with the same product name as input product
        products = [prod for prod in data_list[loc_time] 
                    if list(prod.keys())[0] == a_prod[1]]
        if len(products) > 0:                    
            # check if any one product has the same bands n mask band loaded
            for item in products:
                if set(item[a_prod[1]]['data'].data_vars) == set(a_prod[2]):
                    if item[a_prod[1]]['mask_band'] == a_prod[3]:
                        loaded = True
                        break         
    return loaded      


# Functions of loading data in four different ways
def single_loc_process(prod_info, acq_min, acq_max, lon, lat, window_size, 
                       no_partial_scenes):
    
    loaded_data = get_data_opensource(prod_info, lon, lat, acq_min, acq_max, 
                                      window_size, no_partial_scenes)        
    if loaded_data[prod_info[1]]['data'].data_vars and len(loaded_data[prod_info[1]]['data'].time) > 0:
        return loaded_data
    else:
        print ('{}: No data available\r'.format(prod_info[1]))
        log.info('{}: No data available\r'.format(prod_info[1]))
        

def multiple_loc_process(prod_info, acq_min, acq_max, lon_lat_file, 
                         window_size, no_partial_scenes, input_data_list):
    
    with open(lon_lat_file, 'r') as loc_file:
        all_locs = loc_file.readlines()
    
    for a_loc in all_locs:
        lon = float(a_loc.split(',')[1].strip())
        lat = float(a_loc.split(',')[0].strip())
        loc_id = a_loc.split(',')[2].strip()
        log.info('{}, {}, {}'.format(lon, lat, loc_id))
        
        kwargs = {'loc': (lon, lat)}
        if not aleady_loaded(prod_info, acq_min, acq_max, input_data_list, 
                             **kwargs):        
            loaded_data = get_data_opensource(prod_info, lon, lat, acq_min, 
                                              acq_max,  window_size, 
                                              no_partial_scenes) 
                        
            if loaded_data[prod_info[1]]['data'].data_vars:            
                if ((lon, lat), (acq_min, acq_max)) not in input_data_list:
                    input_data_list[((lon, lat), (acq_min, acq_max))] = []
                input_data_list[((lon, lat), (acq_min, acq_max))].append(loaded_data)
            else:
                log.info('{}: No data available\r'.format(prod_info[1])) 
            
    return input_data_list


def single_shape_process(prod_info, acq_min, acq_max, shapefile, 
                         no_partial_scenes):
    
    loaded_data = get_data_opensource_shapefile(prod_info, acq_min, acq_max, 
                                                shapefile, no_partial_scenes) 

    if loaded_data[prod_info[1]]['data'].data_vars:
        return loaded_data
    else:
        log.info('{}: No data available\r'.format(prod_info[1]))
        

def multi_shape_process(prod_info, acq_min, acq_max, multi_shape_file, 
                        no_partial_scenes, input_data_list):
    
    with open(multi_shape_file, 'r') as loc_file:
        all_locs = loc_file.readlines()
        
    for a_shapefile in all_locs:  
        a_shapefile = a_shapefile.strip()
        log.info(a_shapefile)
        
        kwargs = {'loc': a_shapefile}
        if not aleady_loaded(prod_info, acq_min, acq_max, input_data_list, 
                             **kwargs):
            loaded_data = get_data_opensource_shapefile(prod_info, acq_min, 
                                                        acq_max, a_shapefile, 
                                                        no_partial_scenes) 
            
            if loaded_data[prod_info[1]]['data'].data_vars:
                if (a_shapefile, (acq_min, acq_max)) not in input_data_list:
                    input_data_list[(a_shapefile, (acq_min, acq_max))] = []
                input_data_list[(a_shapefile, (acq_min, acq_max))].append(loaded_data)
            else:
                log.info('{}: No data available\r'.format(prod_info[1])) 
            
    return input_data_list
    
    
def convert2original_loc_time(loc_time):
    if '.shp' in loc_time:
        orig_loc_time = (loc_time.split(' and ')[0], 
                         eval(loc_time.split(' and ')[1]))
    else:
        orig_loc_time = (eval(loc_time.split(' and ')[0]), 
                         eval(loc_time.split(' and ')[1]))
        
    return orig_loc_time


def draw_stat(plot_info, label, min_reflect, max_reflect, **kwargs):
    plot_data_list = [] 
    range_min_value = 10000
    range_max_value = 0
    for key, value in plot_info.items():        
        data = value['data']
        colour = value['colour']
        
        plot_band = kwargs[key] 
        band_data = data[plot_band] 
               
        # mean value for all scenes over the polygon area
        mean = band_data.mean(dim=('x', 'y')).mean().values
        std = band_data.mean(dim=('x', 'y')).std().values        
        
        # mean values for each scene over the polygon area
        mean_list = band_data.mean(dim=('x', 'y')).values 
        
        time_values_orig = band_data.time.values
        time_values = [datetime.strptime(str(d), '%Y-%m-%dT%H:%M:%S.%f000').date() for d in time_values_orig] 
        start_time = time_values[0]
        end_time = time_values[-1]

        plot_data = dict(        
            name = '{}_{}'.format(key, plot_band),
            x = time_values,
            y = mean_list,
            line = {
                'color': colour,
                'width': 1,}
            )

        plot_data_list.append(plot_data)

        plot_mean = dict(        
            name = '{}_{}_mean'.format(key, plot_band),
            x = [start_time, end_time],
            y = [mean, mean],
            line = {
                'color': colour,
                'width': 1,
                'dash': 'dash',}
            )
        plot_data_list.append(plot_mean)

        plot_std_pos = dict(        
            name = '{}_{}_std'.format(key, plot_band),
            x = [start_time, end_time],
            y = [mean+std, mean+std],
            line = {
                'color': colour,
                'width': 1,
                'dash': 'dashdot',}
            )
        plot_data_list.append(plot_std_pos)

        plot_std_nag = dict(        
            name = '{}_{}_std'.format(key, plot_band),
            x = [start_time, end_time],
            y = [mean-std, mean-std],
            line = {
                'color': colour,
                'width': 1,
                'dash': 'dashdot',}
            )
        plot_data_list.append(plot_std_nag)
                
        # decide the proper display range
        if min_reflect == '' and max_reflect == '':        
            # max n min value for all scenes over polygon area to get yaxis range
            min_value = int(band_data.mean(dim=('x', 'y')).min().values)
            max_value = int(band_data.mean(dim=('x', 'y')).max().values)
            if min_value < range_min_value:
                range_min_value = min_value
            if max_value > range_max_value:
                range_max_value = max_value
    
    if min_reflect == '' and max_reflect == '':    
        min_reflect = range_min_value
        max_reflect = range_max_value
    
    # avoid the error due to time delay
    if min_reflect == '':
        min_reflect = 0
    if max_reflect == '':
        max_reflect = 10000
        
    fig = dict(data=plot_data_list, 
               layout={
                       'title': str(label), 
                       'yaxis': {'range': [0.95*int(min_reflect), 
                                           1.05*int(max_reflect)]}
                      })                      
                      
    plotly.offline.iplot(fig, filename='spectrum')
     

def create_sub_folder(root, sub_folder): 
    output = pjoin(root, sub_folder)
    if not os.path.exists(output):
        os.makedirs(output)
    
    return output

    
def produce_ga_output(sub_type, ard, ga_fd_ds, output_file, ga_fields):
       
    band_no = {'LANDSAT_5': {'blue':'band_1', 'green':'band_2', 'red':'band_3', 
                             'nir':'band_4',  'swir1':'band_5', 
                             'swir2':'band_7'},
               'LANDSAT_7': {'blue':'band_1', 'green':'band_2', 'red':'band_3', 
                             'nir':'band_4', 'swir1':'band_5', 
                             'swir2':'band_7'},
               'LANDSAT_8': {'coastal_aerosol':'band_1', 'blue':'band_2', 
                             'green':'band_3', 'red':'band_4', 'nir':'band_5', 
                             'swir1':'band_6', 'swir2':'band_7'}
              }
                    
    with open(output_file, 'w') as csv_file:                                                                                
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(ga_fields) 
        
        for band in ard.data_vars:
            if band.split('_')[0] == sub_type and 'contiguity' not in band:
                band_info = ard[band]
                
                for a_time in list(band_info.time.values):
                    date = str(a_time)[:19]
                    # sr statistic info
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")                
                        mean_sr = np.nanmean(band_info.loc[a_time].values)
                        min_sr = np.nanmin(band_info.loc[a_time].values)
                        max_sr = np.nanmax(band_info.loc[a_time].values)
                        std_sr = np.nanstd(band_info.loc[a_time].values)
                        variance_sr = np.nanvar(band_info.loc[a_time].values)

                    valid_pixel_per = np.count_nonzero(~np.isnan(band_info.loc[a_time].values)) * 100/ band_info.loc[a_time].values.size
                    
                    # info from other bands
                    solar_azimuth = np.nanmean(ard.solar_azimuth.loc[a_time].values)
                    solar_zenith = np.nanmean(ard.solar_zenith.loc[a_time].values)
                    azimuthal_exiting = np.nanmean(ard.azimuthal_exiting.loc[a_time].values)
                    azimuthal_incident = np.nanmean(ard.azimuthal_incident.loc[a_time].values)
                    exiting = np.nanmean(ard.exiting.loc[a_time].values)
                    incident = np.nanmean(ard.incident.loc[a_time].values)
                    
                    # info from metadata 
                    sat = ''
                    sensor = ''
                    aerosol = ''
                    brdf_geo = ''
                    brdf_iso = ''
                    brdf_vol = ''
                    ozone = ''
                    water_vapour = ''
                    cloud_cover_per = ''
                            
                    for ds in ga_fd_ds:
                        ds_time = '{}T{}'.format(str(ds.metadata_doc['extent']['center_dt'])[:10], 
                                                 str(ds.metadata_doc['extent']['center_dt'])[11:26])
                        
                        if ds_time[:16] in str(a_time):                
                            sat = ds.metadata_doc['platform']['code']
                            sensor = ds.metadata_doc['instrument']['name']

                            band_no_prefix = ''.join(band.split('_')[1:])
                            if band_no_prefix == 'coastalaerosol':
                                band_no_prefix = 'coastal_aerosol'

                            if band_no_prefix == 'coastal_aerosol' and sat != 'LANDSAT_8':
                                continue
  
                            if 'aerosol' in ds.metadata_doc['lineage']['ancillary']:
                                aerosol = ds.metadata_doc['lineage']['ancillary']['aerosol']['value']
                            if 'brdf_geo_{}'.format(band_no[sat][band_no_prefix]) in ds.metadata_doc['lineage']['ancillary']:
                                brdf_geo = ds.metadata_doc['lineage']['ancillary']['brdf_geo_{}'.format(band_no[sat][band_no_prefix])]['value']                           
                            if 'brdf_iso_{}'.format(band_no[sat][band_no_prefix]) in ds.metadata_doc['lineage']['ancillary']:
                                brdf_iso = ds.metadata_doc['lineage']['ancillary']['brdf_iso_{}'.format(band_no[sat][band_no_prefix])]['value']
                            if 'brdf_vol_{}'.format(band_no[sat][band_no_prefix]) in ds.metadata_doc['lineage']['ancillary']:
                                brdf_vol = ds.metadata_doc['lineage']['ancillary']['brdf_vol_{}'.format(band_no[sat][band_no_prefix])]['value']
                            if 'ozone' in ds.metadata_doc['lineage']['ancillary']:
                                ozone = ds.metadata_doc['lineage']['ancillary']['ozone']['value']
                            if 'water_vapour' in ds.metadata_doc['lineage']['ancillary']:
                                water_vapour = ds.metadata_doc['lineage']['ancillary']['water_vapour']['value']
                            if 'other_metadata' in ds.metadata_doc['lineage']['source_datasets']:
                                if 'IMAGE_ATTRIBUTES' in ds.metadata_doc['lineage']['source_datasets']['other_metadata']:
                                    if 'cloud_cover_percentage' in ds.metadata_doc['lineage']['source_datasets']['other_metadata']['IMAGE_ATTRIBUTES']:
                                        cloud_cover_per = ds.metadata_doc['lineage']['source_datasets']['other_metadata']['IMAGE_ATTRIBUTES']['CLOUD_COVER']                                   
                          
                            break                                
                            
                    csv_writer.writerow([band, date, sat, sensor, mean_sr, min_sr, max_sr, std_sr, variance_sr, 
                                         valid_pixel_per, aerosol, brdf_geo, brdf_iso, brdf_vol, 
                                         ozone, water_vapour, cloud_cover_per, solar_azimuth, solar_zenith,
                                         azimuthal_exiting, azimuthal_incident, exiting, incident])
                                 
                        
def match_usgs_to_nbart_null(usgs_l2, match_ard):
    # find the nbart data of match_ard
    ard_useful_bands = [band for band in match_ard.data_vars 
                        if 'nbart_' in band and 'contiguity' not in band]
    ard_nbart = match_ard[ard_useful_bands]
     
    # mask the null pixels for USGS as NBART                      
    nbart_nan = xr.ufuncs.isnan(ard_nbart)                    
    for band in ard_nbart.data_vars:
        band_no_prefix = ''.join(band.split('_')[1:])
        if band_no_prefix == 'coastalaerosol':
            band_no_prefix = 'coastal_aerosol'
        usgs_l2[band_no_prefix] = usgs_l2[band_no_prefix].where(~nbart_nan[band].values, np.nan)
        
    return usgs_l2                                                          
                       
                       
def produce_usgs_output(usgs_l2, usgs_fd_ds, output_file, usgs_fields, 
                        usgs_useless_bands):                 
    # usgs output
    band_interest = list(usgs_l2.data_vars)    
                 
    with open(output_file, 'w') as csv_file: 
        csv_writer = csv.writer(csv_file) 
        csv_writer.writerow(usgs_fields)
    
        for band in band_interest:
            if band not in usgs_useless_bands:
                band_info = usgs_l2[band]
                for time in list(band_info.time.values):
                    date = str(time)[:19]
    
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        mean_sr = np.nanmean(band_info.loc[time].values)
                        min_sr = np.nanmin(band_info.loc[time].values)
                        max_sr = np.nanmax(band_info.loc[time].values)
                        std_sr = np.nanstd(band_info.loc[time].values)
                        variance_sr = np.nanvar(band_info.loc[time].values)
    
                    valid_pixel_per = np.count_nonzero(~np.isnan(band_info.loc[time].values)) * 100/ band_info.loc[time].values.size                
    
                    for ds in usgs_fd_ds:
                        if str(ds.metadata_doc['extent']['center_dt'])[:16] in str(time):
                            sat = ds.metadata_doc['platform']['code']
                            sensor = ds.metadata_doc['instrument']['name']
                            break
                        
                    sr_atmos_opacity = ''
                    sr_aerosol = ''
                    if sat != 'LANDSAT_8':
                        sr_atmos_opacity = np.nanmean(usgs_l2.sr_atmos_opacity.loc[time].values) * 0.001
                    else: 
                        sr_aerosol = np.nanmean(usgs_l2.sr_aerosol.loc[time].values)
                        if sr_aerosol in [66, 68, 72, 80, 96, 100]:
                            sr_aerosol = 'Low-level aerosol'
                        elif sr_aerosol in [130, 132, 136, 144, 160, 164]:    
                            sr_aerosol = 'Medium-level aerosol'
                        elif sr_aerosol in [194, 196, 200, 208, 224, 228]:
                            sr_aerosol = 'High-level aerosol'
                
                    csv_writer.writerow([band, date, sat, sensor, mean_sr, min_sr, 
                                         max_sr, std_sr, variance_sr, 
                                         valid_pixel_per, 
                                         sr_atmos_opacity, sr_aerosol])       
                                         
                                         
def produce_reports(report_folder, loaded_products_list, common_dates):
    print ('Produce reports ...')  
    
    configFile = './utilities/report_fields.cfg'
    config = configparser.RawConfigParser()
    config.read(configFile)
    
    usgs_fields = ast.literal_eval(config.get('Fields', 'USGS_fields'))
    usgs_useless_bands = ast.literal_eval(config.get('Fields', 'USGS_useless_bands'))
    ga_fields = ast.literal_eval(config.get('Fields', 'GA_fields'))
    
    for key, items_list in loaded_products_list.items():        
        if len(items_list) > 0:
            if '.shp' in key[0]:
                sub_folder = os.path.splitext(os.path.basename(key[0]))[0]
            else:
                sub_folder = '{}_{}'.format(str(int(key[0][0])), 
                                            str(int(key[0][1])))
                                            
            report_loc_folder = create_sub_folder(report_folder, sub_folder)            
        
        for sub_type in ['lambertian', 'nbar', 'nbart']:
            for item in items_list:
                prod_name = list(item.keys())[0]
                prod_data = item[prod_name]['data']
                prod_ds_list = item[prod_name]['find_list']
                
                output_file = pjoin(report_loc_folder, 
                                    '{}_{}_{}_{}.csv'.format(prod_name, 
                                                             sub_type,
                                                             str(key[1][0]), 
                                                             str(key[1][1])))
                if not os.path.isfile(output_file):                                                             
                    print ('Produce {}'.format(output_file))
                    log.info('Produce {}'.format(output_file))
                    
                    if 'ard' in prod_name:                        
                        produce_ga_output(sub_type, prod_data, prod_ds_list, 
                                          output_file, ga_fields)
                    if 'usgs' in prod_name:
                        if sub_type == 'nbart':
                            if common_dates:
                                # find match ard data
                                match_ard = '{}_ard'.format(prod_name.split('_')[0])
                                for a_prod in items_list:
                                    if list(a_prod.keys())[0] == match_ard:
                                        match_ard_data = a_prod[match_ard]['data']
                                        break
                                    
                                prod_data = match_usgs_to_nbart_null(prod_data, 
                                                                     match_ard_data)
                            
                        produce_usgs_output(prod_data, prod_ds_list, 
                                            output_file, usgs_fields, 
                                            usgs_useless_bands)                       
                else:
                    print ('{} already exists !'.format(output_file))
                    log.info('{} already exists !'.format(output_file))