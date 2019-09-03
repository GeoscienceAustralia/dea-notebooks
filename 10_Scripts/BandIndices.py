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


# Define custom functions
def band_indices(ds, index='NDVI', 
                 custom_varname=None, 
                 source='LandsatCollection2'): 
    
    """
    Takes an xarray dataset containing spectral bands, calculates one of a 
    set of remote sensing indices, and adds the resulting array as a new variable 
    in the original dataset.    

    Last modified: September 2019
    Author: Robbi Bishop-Taylor
    
    Parameters
    ----------  
    ds : xarray Dataset
        A two-dimensional or multi-dimensional array with spectral bands named 
        'red', 'green', 'blue', 'nir', 'swir1' or 'swir2'. These bands are used
        as inputs to calculate the selected water index.
    index : str, optional
        A string giving the name of the index to calculate. Valid options:
        'NDVI' (Normalised Difference Vegation Index, Rouse 1973)
        'EVI' (Enhanced Vegetation Index, Huete 2002),
        'LAI' (Leaf Area Index, Boegh 2002),
        'SAVI' (Soil Adjusted Vegetation Index, Huete 1988),
        'NDMI' (Normalised Difference Moisture Index, Gao 1996),
        'NBR' (Normalised Burn Ratio, Lopez Garcia 1991),
        'BAI' (Burn Area Index, Martin 1998),
        'NDBI' (Normalised Difference Built-Up Index, Zha 2003),
        'NDSI' (Normalised Difference Snow Index, Hall 1995),
        'NDWI' (Normalised Difference Water Index, McFeeters 1996), 
        'MNDWI' (Modified Normalised Difference Water Index, Xu 1996), 
        'AWEI_ns (Automated Water Extraction Index - no shadows, Feyisa 2014)',
        'AWEI_sh' (Automated Water Extraction Index - shadows, Feyisa 2014), 
        'WI' (Water Index, Fisher 2016),
        'TCW' (Tasseled Cap Wetness, Crist 1985),
        'TCG' (Tasseled Cap Greeness, Crist 1985),
        'TCB' (Tasseled Cap Brightness, Crist 1985),
        'CMR' (Clay Minerals Ratio, Drury 1987),
        'FMR' (Ferrous Minerals Ratio, Segal 1982),
        'IOR' (Iron Oxide Ratio, Segal 1982)
        Defaults to 'NDVI'.        
    custom_varname : str, optional
        By default, the function will return the original dataset with a new
        index variable named after `index` (e.g. 'NDVI'). To specify
        a custom name instead, you can supply e.g. `custom_varname='custom_name'`. 
    collection : str, optional
        An optional string that tells the function what dataset or data 
        collection is being used to calculate the index. This is necessary 
        because Landsat Collection 2, Landsat Collection 3 and Sentinel 2 use
        different names for bands covering a similar spectra. Valid options
        are 'LandsatCollection2', 'LandsatCollection3' and 'Sentinel2';
        defaults to 'LandsatCollection2'.
        
    Returns
    -------
    ds : xarray Dataset
        The original xarray Dataset inputted into the function, with a new band
        containing the remote sensing index as a DataArray.
    """           
   
    # Dictionary containing remote sensing index band recipes
    index_dict = {
                  # Normalised Difference Vegation Index, Rouse 1973
                  'NDVI': lambda ds: (ds.nir - ds.red) / (ds.nir + ds.red),
        
                  # Enhanced Vegetation Index, Huete 2002
                  'EVI': lambda ds: ((2.5 * (ds.nir - ds.red)) / 
                                     (ds.nir + 6 * ds.red - 7.5 * ds.blue + 1)),
        
                  # Leaf Area Index, Boegh 2002
                  'LAI': lambda ds: (3.618 * ((2.5 * (ds.nir - ds.red)) / 
                                     (ds.nir + 6 * ds.red - 7.5 * ds.blue + 1))
                                     - 0.118),
        
                  # Soil Adjusted Vegetation Index, Huete 1988
                  'SAVI': lambda ds: ((1.5 * (ds.nir - ds.red)) / 
                                      (ds.nir + ds.red + 0.5)),
        
                  # Normalised Difference Moisture Index, Gao 1996 
                  'NDMI': lambda ds: (ds.nir - ds.swir1) / (ds.nir + ds.swir1),
        
                  # Normalised Burn Ratio, Lopez Garcia 1991
                  'NBR': lambda ds: (ds.nir - ds.swir1) / (ds.nir + ds.swir1),
        
                  # Burn Area Index, Martin 1998
                  'BAI': lambda ds: (1.0 / ((0.10 - ds.red) ** 2 + 
                                            (0.06 - ds.nir) ** 2)),
        
                  # Normalised Difference Built-Up Index, Zha 2003
                  'NDBI': lambda ds: (ds.swir1 - ds.nir) / (ds.swir1 + ds.nir),
        
                  # Normalised Difference Snow Index, Hall 1995
                  'NDSI': lambda ds: (ds.green - ds.swir1) / (ds.green + ds.swir1),
        
                  # Normalised Difference Water Index, McFeeters 1996
                  'NDWI': lambda ds: (ds.green - ds.nir) / (ds.green + ds.nir),
        
                  # Modified Normalised Difference Water Index, Xu 2006
                  'MNDWI': lambda ds: (ds.green - ds.swir1) / (ds.green + ds.swir1),
        
                  # Automated Water Extraction Index (no shadows), Feyisa 2014
                  'AWEI_ns': lambda ds: (4 * (ds.green - ds.swir1) -
                                        (2.5 * ds.nir * + 2.75 * ds.swir2)),
        
                  # Automated Water Extraction Index (shadows), Feyisa 2014
                  'AWEI_sh': lambda ds: (ds.blue + 2.5 * ds.green - 
                                         1.5 * (ds.nir + ds.swir1) - 2.5 * ds.swir2),
    
                  # Water Index, Fisher 2016
                  'WI': lambda ds: (1.7204 + 171 * ds.green + 3 * ds.red - 
                                    70 * ds.nir - 45 * ds.swir1 - 71 * ds.swir2),
        
                  # Tasseled Cap Wetness, Crist 1985
                  'TCW': lambda ds: (0.0315 * ds.blue + 0.2021 * ds.green + 
                                     0.3102 * ds.red + 0.1594 * ds.nir + 
                                    -0.6806 * ds.swir1 + -0.6109 * ds.swir2),
        
                  # Tasseled Cap Greeness, Crist 1985
                  'TCG': lambda ds: (-0.1603 * ds.blue + -0.2819 * ds.green + 
                                     -0.4934 * ds.red + 0.7940 * ds.nir + 
                                     -0.0002 * ds.swir1 + -0.1446 * ds.swir2),
        
                  # Tasseled Cap Brightness, Crist 1985
                  'TCB': lambda ds: (0.2043 * ds.blue + 0.4158 * ds.green + 
                                     0.5524 * ds.red + 0.5741 * ds.nir + 
                                     0.3124 * ds.swir1 + -0.2303 * ds.swir2),
    
                  # Clay Minerals Ratio, Drury 1987
                  'CMR': lambda ds: (ds.swir1 / ds.swir2),
        
                  # Ferrous Minerals Ratio, Segal 1982
                  'FMR': lambda ds: (ds.swir1 / ds.nir),
        
                  # Iron Oxide Ratio, Segal 1982
                  'IOR': lambda ds: (ds.red / ds.blue)
    } 
    
    # Select a water index function based on 'water_index'    
    index_func = index_dict[index]
    
    # Rename bands to a consistent format if either 'Collection3'
    # or 'Sentinel2' is specified by `source`
    if source == 'Collection3':
        
        # Dictionary mapping full data names to simpler 'red' alias names
        bandnames_dict = {'nbart_red': 'red', 'nbart_green': 'green',
                          'nbart_blue': 'blue', 'nbart_nir': 'nir',
                          'nbart_swir_1': 'swir1', 'nbart_swir_2': 'swir2',
                          'nbar_red': 'red', 'nbar_green': 'green',
                          'nbar_blue': 'blue', 'nbar_nir': 'nir', 
                          'nbar_swir_1': 'swir1', 'nbar_swir_2': 'swir2'}

        # Rename bands in dataset to use simple names (e.g. 'red')
        bands_to_rename = {a: b for a, b in bandnames_dict.items() if a in ds.variables}
        
    elif source == 'Sentinel2':
        
        # Dictionary mapping full data names to simpler 'red' alias names
        bandnames_dict = {'nbart_red': 'red', 'nbart_green': 'green',
                          'nbart_blue': 'blue', 'nbart_nir_1': 'nir',
                          'nbart_swir_2': 'swir1', 'nbart_swir_3': 'swir2',
                          'nbar_red': 'red', 'nbar_green': 'green',
                          'nbar_blue': 'blue', 'nbar_nir': 'nir',
                          'nbar_swir_2': 'swir1', 'nbar_swir_3': 'swir2'}

        # Rename bands in dataset to use simple names (e.g. 'red')
        bands_to_rename = {a: b for a, b in bandnames_dict.items() if a in ds.variables}

    elif source == 'Collection2':
        
        # For the DEA Collection 2, pass an empty dict as no bands need renaming
        bands_to_rename = {}

    
    # Apply water index function to data and add to input dataset. If a custom name
    # is supplied for the output water index variable, use it.
    if custom_varname:        
        
        # Apply function after normalising to a 0.0-1.0 range by dividing by 10,000
        ds[custom_varname] = index_func(ds.rename(bands_to_rename) / 10000.0)
        
    else:
        
        # Apply function after normalising to a 0.0-1.0 range by dividing by 10,000
        ds[index] = index_func(ds.rename(bands_to_rename) / 10000.0)
    
    # Return input dataset with added water index variable
    return ds



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
