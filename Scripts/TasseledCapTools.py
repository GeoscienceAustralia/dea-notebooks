## TasseledCapTools.py

'''
TasseledCapTools contains a set of python functions to use with the outputs of tasseled cap
transforms (such as produced by BandIndices.tasseled_cap). 
Thresholded tasseled cap is an intermediate step in tasseled cap percentage exceedance
but is useful in its own right for producing hovmoller plots.
TasseledCapTools is also useful in situations where speed and memory are issues. 

This file requires the BandIndices.py python script from dea-notebooks/Scripts

datacube-stats includes the function TCWStats.TCW stats calculates mean brightness, wetness,
and greenness, percentage exceedances and standard deviations. It allows thresholds and 
can be loaded using:

from datacube_stats.statistics import TCWStats

TasseledCapTools is intended for applications where TCWStats doesn't return intermediate
results, or where TCWStats handles memory differently to TasseledCapTools.
Last modified: April 2021
Authors: Bex Dunn, Robbi Bishop-Taylor

Available functions:
    thresholded_tasseled_cap
    pct_exceedance_tasseled_cap

'''
import dask
import os
import sys
import xarray as xr


# Import external functions from dea-notebooks
sys.path.append(os.path.expanduser('~/dea-notebooks/Scripts/'))
#from BandIndices import tasseled_cap --this needs to be replaced with bandindices
#mport dea_tools.bandindices


def thresholded_tasseled_cap(sensor_data, tc_bands=['greenness', 'brightness', 'wetness'],
                             greenness_threshold=700,brightness_threshold=4000,
                             wetness_threshold=-600, drop=True, drop_tc_bands=True):
    """Computes thresholded tasseled cap wetness, greenness and brightness bands 
    from a six band xarray dataset, and returns a new xarray dataset with old bands
    optionally dropped.
    Last modified: June 2018
    Authors: Bex Dunn, Robbi Bishop-Taylor

    :attr sensor_data: input xarray dataset with six Landsat bands
    :attr tc_bands: list of tasseled cap bands to compute
    (valid options: 'wetness', 'greenness','brightness')
    :attr greenness_threshold: optional threshold as float
    :attr brightness_threshold: optional threshold as float
    :attr wetness_threshold: optional threshold as float
    :attr drop: if 'drop = False', return all original Landsat bands
    :attr drop_tc_bands: if 'drop_tc_bands = False', return all unthresholded tasseled 
    cap bands as well as the thresholded bands
    :returns: xarray dataset with newly computed thresholded tasseled cap bands
    """

    # Copy input dataset
    output_array = sensor_data.copy(deep=True)

    # Coefficients for each tasseled cap band
    wetness_coeff = {'blue': 0.0315, 'green': 0.2021, 'red': 0.3102,
                     'nir': 0.1594, 'swir1': -0.6806, 'swir2': -0.6109}

    greenness_coeff = {'blue': -0.1603, 'green': -0.2819, 'red': -0.4934,
                       'nir': 0.7940, 'swir1': -0.0002, 'swir2': -0.1446}

    brightness_coeff = {'blue': 0.2043, 'green': 0.4158, 'red': 0.5524,
                        'nir': 0.5741, 'swir1': 0.3124, 'swir2': 0.2303} 


    # Dict to use correct coefficients for each tasseled cap band
    analysis_coefficient = {'wetness': wetness_coeff,
                            'greenness': greenness_coeff,
                            'brightness': brightness_coeff}

    #make dictionary of thresholds for wetness, brightness and greenness
    ###FIXME:add statistical and/or secant thresholding options?

    analysis_thresholds = {'wetness_threshold': wetness_threshold,
                           'greenness_threshold': greenness_threshold,
                           'brightness_threshold': brightness_threshold}

    # For each band, compute tasseled cap band and add to output dataset
    for tc_band in tc_bands:
        # Create xarray of coefficient values used to multiply each band of input
        coeff = xr.Dataset(analysis_coefficient[tc_band])
        sensor_coeff = sensor_data * coeff
        # Sum all bands
        output_array[tc_band] = sensor_coeff.blue + sensor_coeff.green +                                                 sensor_coeff.red + sensor_coeff.nir +                                                 sensor_coeff.swir1 + sensor_coeff.swir2
        output_array[str(tc_band+'_thresholded')]=output_array[tc_band].where(output_array[tc_band]>analysis_thresholds[str(tc_band+'_threshold')])                      
        if drop_tc_bands:
            output_array =output_array.drop(tc_band)

    # If drop = True, remove original bands
    if drop:
        bands_to_drop = list(sensor_data.data_vars)
        output_array = output_array.drop(bands_to_drop)


    return output_array

# def pct_exceedance_tasseled_cap(sensor_data, tc_bands=['greenness', 'brightness', 'wetness'],
#                              greenness_threshold=700,brightness_threshold=4000,
#                              wetness_threshold=-600, drop=True, drop_tc_bands=True):
#     '''counts the number of thresholded tasseled cap scenes per pixel and divides by the 
#     number of tasseled cap scenes per pixel. Returns the percentage of scenes exceeding the
#     tasselled cap thresholds for the requested tasseled cap bands as an xarray.

#     Last modified: June 2018
#     Authors: Bex Dunn, Robbi Bishop-Taylor

#     :attr sensor_data: input xarray dataset with six Landsat bands
#     :attr tc_bands: list of tasseled cap bands to compute
#     (valid options: 'wetness', 'greenness','brightness')
#     :attr greenness_threshold: optional threshold as float
#     :attr brightness_threshold: optional threshold as float
#     :attr wetness_threshold: optional threshold as float
#     :attr drop: if 'drop = False', return all original Landsat bands
#     :attr drop_tc_bands: if 'drop_tc_bands = False', return all unthresholded tasseled 
#     cap bands as well as the thresholded bands
#     :attr tc_kwargs: a dictionary of this function's input arguments needed by
#     the nested tasseled_cap function
#     :attr thresholded tc_kwargs:a dictionary of this function's input arguments needed by
#     the nested thresholded_tasseled_cap function
#     :returns: xarray dataset with the percentage exceedance of each threshold. 
#     ##FIXME - may want to change this so that you don't get the same thing for all time.
#     """
#     '''
#     tc_kwargs={'sensor_data':sensor_data, 
#                'tc_bands':tc_bands,
#                'drop':drop}
    
#     thresholded_tc_kwargs={**tc_kwargs, 
#                            'greenness_threshold': greenness_threshold,
#                            'brightness_threshold': brightness_threshold,
#                            'wetness_threshold':wetness_threshold,
#                            'drop_tc_bands':drop_tc_bands}
                               
#     pct_exceedance_array = sensor_data.copy(deep=True)
#     tc_bands=['greenness', 'brightness', 'wetness']
#     for tc_band in tc_bands:
#         pct_exceedance_array[str(tc_band+'_pct_exceedance')] = thresholded_tasseled_cap(**thresholded_tc_kwargs)[str(tc_band+'_thresholded')].count(dim='time')/        tasseled_cap(**tc_kwargs)[tc_band].count(dim='time')
#     # If drop = True, remove original bands
#     if drop:
#         bands_to_drop = list(sensor_data.data_vars)
#         pct_exceedance_array = pct_exceedance_array.drop(bands_to_drop)

#     return pct_exceedance_array
   

