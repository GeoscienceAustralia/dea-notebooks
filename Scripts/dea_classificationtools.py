## dea_classificationtools.py
'''
Description: This file contains a set of python functions for applying machine learning classifiying remote sensing data from Digital Earth Australia.

License: The code in this notebook is licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth Australia data is licensed under the Creative Commons by Attribution 4.0 license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: September 2019

Authors: Richard Taylor, ...

'''

import numpy as np
from xarray.core.dataset import Dataset

#'Wrappers' to translate xarrays to np arrays and back for interfacing with sklearn models

def _sklearn_flatten(input_xr):
    """
    Reshape a DataArray or Dataset with spatial (and optionally temporal) structure into 
    an np.array with the spatial and temporal dimensions flattened into one dimension.
    
    This flattening procedure enables DataArrays and Datasets to be used to train and predict
    with sklearn models.
    
    Last modified: September 2019
    
    Parameters
    ----------  
        input_xr : a DataArray or Dataset. Must have dimensions 'x' and 'y', may have dimension 'time'.
                   Dimensions other than 'x', 'y' and 'time' are unaffected by the flattening.
    
    """
    
    #cast input Datasets to DataArray
    if isinstance(input_xr,Dataset):
        input_xr = input_xr.to_array()
    
    #stack across pixel dimensions, handling timeseries if necessary
    if 'time' in input_xr.dims:
        stacked = input_xr.stack(z=['x','y','time'])
    else:
        stacked = input_xr.stack(z=['x','y'])
        
    #finding 'bands' dimensions in each pixel - these will not be flattened as their context is important for sklearn
    pxdims = []
    for dim in stacked.dims:
        if dim != 'z':
            pxdims.append(dim)
    
    #mask NaNs - we mask pixels with NaNs in *any* band, because sklearn cannot accept NaNs as input
    mask = np.isnan(stacked)
    if len(pxdims)!=0:
        mask = mask.any(dim=pxdims)
    
    #the dimension we are masking along ('z') needs to be the first dimension in the underlying np array for
    #the boolean indexing to work
    stacked = stacked.transpose('z',*pxdims)
    input_np = stacked.data[~mask]
    
    return input_np

# def _sklearn_unflatten(output_np,input_xr):
    
    
    
    
    
    