## dea_bandindices.py
'''
Description: This file contains a set of python functions for computing remote sensing band indices on Digital Earth Australia data.

License: The code in this notebook is licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth Australia data is licensed under the Creative Commons by Attribution 4.0 license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: September 2019

'''


# Define custom functions
def calculate_indices(ds,
                      index='NDVI',
                      custom_varname=None,
                      source='LandsatCollection3'):
    """
    Takes an xarray dataset containing spectral bands, calculates one of
    a set of remote sensing indices, and adds the resulting array as a 
    new variable in the original dataset.  
    
    Last modified: September 2019
    
    Parameters
    ----------  
    ds : xarray Dataset
        A two-dimensional or multi-dimensional array with containing the 
        spectral bands required to calculate the index. These bands are 
        used as inputs to calculate the selected water index.
    index : str, optional
        A string giving the name of the index to calculate:
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
        'AWEI_ns (Automated Water Extraction Index,
                  no shadows, Feyisa 2014)',
        'AWEI_sh' (Automated Water Extraction Index,
                   shadows, Feyisa 2014), 
        'WI' (Water Index, Fisher 2016),
        'TCW' (Tasseled Cap Wetness, Crist 1985),
        'TCG' (Tasseled Cap Greeness, Crist 1985),
        'TCB' (Tasseled Cap Brightness, Crist 1985),
        'CMR' (Clay Minerals Ratio, Drury 1987),
        'FMR' (Ferrous Minerals Ratio, Segal 1982),
        'IOR' (Iron Oxide Ratio, Segal 1982)
        Defaults to 'NDVI'.        
    custom_varname : str, optional
        By default, the function will return the original dataset with 
        a new index variable named after `index` (e.g. 'NDVI'). To 
        specify a custom name instead, you can supply e.g. 
        `custom_varname='custom_name'`. 
    collection : str, optional
        An optional string that tells the function what dataset or data 
        collection is being used to calculate the index. This is 
        necessary because Landsat Collection 2, Landsat Collection 3 and
        Sentinel 2 use different names for bands covering a similar 
        spectra. Valid options are 'LandsatCollection2', 
        'LandsatCollection3' and 'Sentinel2'; defaults to 
        'LandsatCollection2'.
        
    Returns
    -------
    ds : xarray Dataset
        The original xarray Dataset inputted into the function, with a 
        new varible containing the remote sensing index as a DataArray.
    """

    # Dictionary containing remote sensing index band recipes
    index_dict = {
                  # Normalised Difference Vegation Index, Rouse 1973
                  'NDVI': lambda ds: (ds.nir - ds.red) /
                                     (ds.nir + ds.red),

                  # Enhanced Vegetation Index, Huete 2002
                  'EVI': lambda ds: ((2.5 * (ds.nir - ds.red)) /
                                     (ds.nir + 6 * ds.red -
                                      7.5 * ds.blue + 1)),

                  # Leaf Area Index, Boegh 2002
                  'LAI': lambda ds: (3.618 * ((2.5 * (ds.nir - ds.red)) /
                                     (ds.nir + 6 * ds.red -
                                      7.5 * ds.blue + 1)) - 0.118),

                  # Soil Adjusted Vegetation Index, Huete 1988
                  'SAVI': lambda ds: ((1.5 * (ds.nir - ds.red)) /
                                      (ds.nir + ds.red + 0.5)),

                  # Normalised Difference Moisture Index, Gao 1996
                  'NDMI': lambda ds: (ds.nir - ds.swir1) /
                                     (ds.nir + ds.swir1),

                  # Normalised Burn Ratio, Lopez Garcia 1991
                  'NBR': lambda ds: (ds.nir - ds.swir1) /
                                    (ds.nir + ds.swir1),

                  # Burn Area Index, Martin 1998
                  'BAI': lambda ds: (1.0 / ((0.10 - ds.red) ** 2 +
                                            (0.06 - ds.nir) ** 2)),

                  # Normalised Difference Built-Up Index, Zha 2003
                  'NDBI': lambda ds: (ds.swir1 - ds.nir) /
                                     (ds.swir1 + ds.nir),

                  # Normalised Difference Snow Index, Hall 1995
                  'NDSI': lambda ds: (ds.green - ds.swir1) /
                                     (ds.green + ds.swir1),

                  # Normalised Difference Water Index, McFeeters 1996
                  'NDWI': lambda ds: (ds.green - ds.nir) /
                                     (ds.green + ds.nir),

                  # Modified Normalised Difference Water Index, Xu 2006
                  'MNDWI': lambda ds: (ds.green - ds.swir1) /
                                      (ds.green + ds.swir1),

                  # Automated Water Extraction Index (no shadows), Feyisa 2014
                  'AWEI_ns': lambda ds: (4 * (ds.green - ds.swir1) -
                                        (2.5 * ds.nir * + 2.75 * ds.swir2)),

                  # Automated Water Extraction Index (shadows), Feyisa 2014
                  'AWEI_sh': lambda ds: (ds.blue + 2.5 * ds.green -
                                         1.5 * (ds.nir + ds.swir1) -
                                         2.5 * ds.swir2),

                  # Water Index, Fisher 2016
                  'WI': lambda ds: (1.7204 + 171 * ds.green + 3 * ds.red -
                                    70 * ds.nir - 45 * ds.swir1 -
                                    71 * ds.swir2),

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

    try:

        # Select a water index function based on 'water_index'
        index_func = index_dict[index]

        # Rename bands to a consistent format if either 'Collection3'
        # or 'Sentinel2' is specified by `source`
        if source == 'LandsatCollection3':

            # Dictionary mapping full data names to simpler 'red' alias names
            bandnames_dict = {
                'nbart_nir': 'nir',
                'nbart_red': 'red',
                'nbart_green': 'green',
                'nbart_blue': 'blue',
                'bart_swir_1': 'swir1',
                'nbart_swir_2': 'swir2',
                'nbar_red': 'red',
                'nbar_green': 'green',
                'nbar_blue': 'blue',
                'nbar_nir': 'nir',
                'nbar_swir_1': 'swir1',
                'nbar_swir_2': 'swir2'
            }

            # Rename bands in dataset to use simple names (e.g. 'red')
            bands_to_rename = {
                a: b for a, b in bandnames_dict.items() if a in ds.variables
            }

        elif source == 'Sentinel2':

            # Dictionary mapping full data names to simpler 'red' alias names
            bandnames_dict = {
                'nbart_red': 'red',
                'nbart_green': 'green',
                'nbart_blue': 'blue',
                'nbart_nir_1': 'nir',
                'nbart_swir_2': 'swir1',
                'nbart_swir_3': 'swir2',
                'nbar_red': 'red',
                'nbar_green': 'green',
                'nbar_blue': 'blue',
                'nbar_nir': 'nir',
                'nbar_swir_2': 'swir1',
                'nbar_swir_3': 'swir2'
            }

            # Rename bands in dataset to use simple names (e.g. 'red')
            bands_to_rename = {
                a: b for a, b in bandnames_dict.items() if a in ds.variables
            }

        elif source == 'LandsatCollection2':

            # Pass an empty dict as no bands need renaming
            bands_to_rename = {}

        # Apply water index function to data and add to input dataset. If a
        # custom name is supplied for the output water index variable, use it.
        if custom_varname:

            # Apply function after normalising to 0.0-1.0 by dividing by 10K
            ds[custom_varname] = index_func(
                ds.rename(bands_to_rename) / 10000.0)

        else:

            # Apply function after normalising to 0.0-1.0 by dividing by 10K
            ds[index] = index_func(ds.rename(bands_to_rename) / 10000.0)

        # Return input dataset with added water index variable
        return ds

    except AttributeError as e:
        raise Exception(
            f'The band equivelent to {str(e).split(" ")[-1]} is missing from '
            f'the input dataset. \nPlease verify that all bands required to '
            f'compute {index} are present in `ds`.'
        )

    except KeyError as e:
        raise Exception(
            f'The selected index {e} is not one of the valid remote sensing '
            f'index options. \n Please see the function documentation for a '
            'full list of valid options for `index`'
        )
        

