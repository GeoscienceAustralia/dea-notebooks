# BandIndices.py
"""
This code allows for the quick calculation of remote sensing band indices.

Date: June 2018
Authors: Claire Krause, Bex Dunn

Available functions:
    calculate indices  : NDVI, GNDVI, NDWI, NDMI
    geological_indices : CMR, FMR, IOR
    tasseled_cap       : Brightness, Greenness, Wetness

"""
#Load modules
import dask
import numpy as np
import xarray as xr

def calculate_indices(ds, index):

    """
    Available indices are all calculated within the same function. If an
    index is requested that is not coded in the function, an error is
    raised.

    Try/except statements are used to account for the different band
    names for Landsat and Sentinel2 data.

    Available indices:
    - NDVI: Normalised Difference Vegetation Index
    - GNDVI: Green Normalised Difference Vegetation Index
    - NDWI: Normalised Difference Water Index
    - NDMI: Normalised Difference Moisture Index

    inputs:
    ds - dataset containing the bands needed for index calculation
    index - str of the index to be calculated

    outputs:
    indexout - result of the index calculation
    
    """

    if index == 'NDWI-nir':
        print('The formula we are using is (green - nir)/(green + nir)')
        try:
            indexout = ((ds.green - ds.nir)/(ds.green + ds.nir))
        except AttributeError:
            try:
                # Assume the user wants to use nbart unless they explicity state otherwise
                indexout = ((ds.nbart_green - ds.nbart_nir_1)/(ds.nbart_green + ds.nbart_nir_1))
            except AttributeError:
                try:
                    indexout = ((ds.nbar_green - ds.nbar_nir_1)/(ds.nbar_green + ds.nbar_nir_1))
                except:
                    print('Error! NDWI requires green and nir bands')
    elif index == 'ModifiedNDWI':
        print('The formula we are using is (green - swir1)/(green + swir1)')
        try:
            indexout = ((ds.green - ds.swir1)/(ds.green + ds.swir1))
        except AttributeError:
            try:
                # Assume the user wants to use nbart unless they explicity state otherwise
                indexout = ((nbart_green - ds.nbart_swir_1)/(nbart_green + ds.nbart_swir_1))
            except AttributeError:
                try:
                    indexout = ((nbar_green - ds.nbar_swir_1)/(nbar_green + ds.nbar_swir_1))
                except:
                    print('Error! NDWI requires green and swir1 bands')
    elif index == 'NDVI':
        print('The formula we are using is (nir - red)/(nir + red)')
        try:
            indexout = ((ds.nir - ds.red)/(ds.nir + ds.red))
        except AttributeError:
            try:
                # Assume the user wants to use nbart unless they explicity state otherwise
                indexout = ((ds.nbart_nir_1 - ds.nbart_red)/(ds.nbart_nir_1 + ds.nbart_red))
            except AttributeError:
                try:
                    indexout = ((ds.nbar_nir_1 - ds.nbar_red)/(ds.nbar_nir_1 + ds.nbar_red))
                except:
                    print('Error! NDVI requires red and nir bands')  
    elif index == 'GNDVI':
        print('The formula we are using is (nir - green)/(nir + green)')
        try:
            indexout = ((ds.nir - ds.green)/(ds.nir + ds.green))
        except AttributeError:
            try:
                # Assume the user wants to use nbart unless they explicity state otherwise
                indexout = ((ds.nbart_nir_1 - ds.nbart_green)/(ds.nbart_nir_1 + ds.nbart_green))
            except AttributeError:
                try:
                    indexout = ((ds.nbar_nir_1 - ds.nbar_green)/(ds.nbar_nir_1 + ds.nbar_green))
                except:
                    print('Error! GNDVI requires green and nir bands')
    elif index == 'NDMI-green':
        print('The formula we are using is (swir1 - green)/(swir1 + green)')
        try:
            indexout = ((ds.swir1 - ds.green)/(ds.swir1 + ds.green))
        except AttributeError:
            try:
                # Assume the user wants to use nbart unless they explicity state otherwise
                indexout = ((ds.nbart_swir_1 - ds.nbart_green)/(ds.nbart_swir_1 + ds.nbart_green))
            except AttributeError:
                try:
                    indexout = ((ds.nbar_swir_1 - ds.nbar_green)/(ds.nbar_swir_1 + ds.nbar_green))
                except:
                    print('Error! NDMI-green requires green and swir1 bands')
    elif index == 'NDMI-nir':
        print('The formula we are using is (nir - swir1)/(nir + swir1)')
        try:
            indexout = ((ds.nir - ds.swir1)/(ds.nir + ds.swir1))
        except AttributeError:
            try:
                # Assume the user wants to use nbart unless they explicity state otherwise
                indexout = ((ds.nbart_nir_1 - ds.nbart_swir_1)/(ds.nbart_nir_1 + ds.nbart_swir_1))
            except AttributeError:
               try: 
                   indexout = ((ds.nbar_nir_1 - ds.nbar_swir_1)/(ds.nbar_nir_1 + ds.nbar_swir_1))
               except:
                   print('Error! NDMI-nir requires nir and swir1 bands')
    try:
        return indexout
    except:
        print('Hmmmmm. I don\'t recognise that index. '
              'Options I currently have are NDVI, GNDVI, NDMI-green, NDMI-nir, NDWI and ModifiedNDWI.')


def geological_indices(ds, index):
    """
    Available indices are all calculated within the same function. If an
    index is requested that is not coded in the function, an error is
    raised.

    Try/except statements are used to account for the different band
    names for Landsat and Sentinel2 data.

    Available geological indices:
    - CMR: Clay Minerals Ratio
    - FMR: Ferrous Minerals Ratio
    - IOR: Iron Oxide Ratio

    inputs:
    ds - dataset containing the bands needed for index calculation
    index - str of the index to be calculated

    outputs:
    indexout - result of the index calculation

    Reference: http://www.harrisgeospatial.com/docs/BackgroundGeologyIndices.html
    """

    if index == 'CMR':
        print('The formula we are using for Clay Minerals Ratio is (swir1 / swir2)')
        try:
            indexout = (ds.swir1 / ds.swir2)
        except AttributeError:
            try:
                indexout = (ds.nbart_swir_1 / ds.nbart_swir_2)
            except AttributeError:
                try:
                    indexout = (ds.nbar_swir_1 / ds.nbar_swir_2)
                except:
                    print('Error! Clay Minerals Ratio requires swir1 and swir2 bands')
    elif index == 'FMR':
        print('The formula we are using for Ferrous Minerals Ratio is (swir1 / nir)')
        try:
            indexout = (ds.swir1 / ds.nir)
        except AttributeError:
            try:
                indexout = (ds.nbart_swir_1 / ds.nbart_nir_1)
            except AttributeError:
                try:
                    indexout = (ds.nbar_swir_1 / ds.nbar_nir_1)
                except:
                    print('Error! Ferrous Minerals Ratio requires swir1 and nir bands')  
    elif index == 'IOR':
        print('The formula we are using for Iron Oxide Ratio is (red / blue)')
        try:
            indexout = (ds.red / ds.blue)
        except AttributeError:
            try:
                indexout = (ds.nbart_red / ds.nbart_blue)
            except AttributeError:
                try:
                    indexout = (ds.nbar_red / ds.nbar_blue)
                except:
                    print('Error! Iron Oxide Ratio requires red and blue bands')
    try:
        return indexout
    except:
        print('Hmmmmm. I don\'t recognise that index. '
              'Options I currently have are CMR, FMR and IOR.')
        
def tasseled_cap(sensor_data, tc_bands=['greenness', 'brightness', 'wetness'],
                 drop=True):
    """   
    Computes tasseled cap wetness, greenness and brightness bands from a six
    band xarray dataset, and returns a new xarray dataset with old bands
    optionally dropped.
    
    Coefficients are from Crist and Cicone 1985 "A TM Tasseled Cap equivalent 
    transformation for reflectance factor data"
    https://doi.org/10.1016/0034-4257(85)90102-6
    
    Last modified: June 2018
    Authors: Robbi Bishop-Taylor, Bex Dunn
    
    :attr sensor_data: input xarray dataset with six Landsat bands
    :attr tc_bands: list of tasseled cap bands to compute
    (valid options: 'wetness', 'greenness','brightness')
    :attr drop: if 'drop = False', return all original Landsat bands
    :returns: xarray dataset with newly computed tasseled cap bands
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

    # For each band, compute tasseled cap band and add to output dataset
    for tc_band in tc_bands:
        # Create xarray of coefficient values used to multiply each band of input
        coeff = xr.Dataset(analysis_coefficient[tc_band])
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
       

# If the module is being run, not being imported! 
# to do this, do the following
# run {modulename}.py)

if __name__=='__main__':
#print that we are running the testing
    print('Testing..')
#import doctest to test our module for documentation
    import doctest
    doctest.testmod()
    print('Testing done')       
