## dea_classificationtools.py
'''
Description: This file contains a set of python functions for applying machine learning classifiying remote sensing data from Digital Earth Australia.

License: The code in this notebook is licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth Australia data is licensed under the Creative Commons by Attribution 4.0 license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, you can file one on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: September 2019

Authors: Richard Taylor, Sean Chua, ...

'''

import numpy as np
import xarray as xr

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
                   
    Returns
    ----------
        input_np : a numpy array corresponding to input_xr.data (or input_xr.to_array().data), with
                   dimensions 'x','y' and 'time' flattened into a single dimension, which is the first
                   axis of the returned array. input_np contains no NaNs.
    
    """
    
    #cast input Datasets to DataArray
    if isinstance(input_xr,xr.Dataset):
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

def _sklearn_unflatten(output_np,input_xr):
    
    """
    Reshape a numpy array with no 'missing' elements (NaNs) and 'flattened' spatiotemporal structure
    into a DataArray matching the spatiotemporal structure of the DataArray 
    
    This enables an sklearn model's prediction to be remapped to the correct pixels in the input
    DataArray or Dataset.
    
    Last modified: September 2019
    
    Parameters
    ----------  
        output_np : a numpy array. The first dimension's length should correspond to the number of 
                    valid (non-NaN) pixels in input_xr.
        input_xr : a DataArray or Dataset. Must have dimensions 'x' and 'y', may have dimension 'time'.
                   Dimensions other than 'x', 'y' and 'time' are unaffected by the flattening.
                   
    Returns
    ----------
        output_xr : a DataArray with the same dimensions 'x', 'y' and 'time' as input_xr, and the same
                    valid (non-NaN) pixels. These pixels are set to match the data in output_np.
    
    """
    
    
    #the output of a sklearn model prediction should just be a numpy array with size matching x*y*time
    #for the input DataArray/Dataset.
    
    #cast input Datasets to DataArray
    if isinstance(input_xr,xr.Dataset):
        input_xr = input_xr.to_array()
    
    #generate the same mask we used to create the input to the sklearn model
    if 'time' in input_xr.dims:
        stacked = input_xr.stack(z=['x','y','time'])
    else:
        stacked = input_xr.stack(z=['x','y'])
    
    
    
    pxdims = []
    for dim in stacked.dims:
        if dim != 'z':
            pxdims.append(dim)
    
    mask = np.isnan(stacked)
    if len(pxdims)!=0:
        mask = mask.any(dim=pxdims)
        
    #handle multivariable output
    output_px_shape = ()
    if len(output_np.shape[1:]):
        output_px_shape = output_np.shape[1:]
    
    #use the mask to put the data in all the right places
    output_ma = np.ma.empty((len(stacked.z),*output_px_shape))
    output_ma[~mask] = output_np
    output_ma.mask = mask
    
    #set the stacked coordinate to match the input
    output_xr = xr.DataArray(output_ma, coords={'z': stacked['z']},dims=['z',*['output_dim_'+str(idx) for idx in range(len(output_px_shape))]])
    
    output_xr = output_xr.unstack()
    
    return output_xr
    

    
    
    

# def _reshape(output,sar_ds):
#     """
#     Method to convert the flat output array of predictions from a sklearn clustering
#     model to an xarray.DataArray with the same shape as the input dataset.

#     Arguments:
#     output -- flat predictions from an sklearn clustering model.
#     sar_ds -- the input (single-scene) SAR dataset which was used to produce the predictions.
    
#     Returns:
#     An xarray.DataArray with the same shape and dimension names as sar_ds.

#     """
    
#     stacked_sar = sar_ds.stack(z=['x','y'])
    
#     stacked_vv = stacked_sar.vv.to_masked_array()
#     stacked_vh = stacked_sar.vh.to_masked_array()
#     try:
#         stacked_vh_vv = stacked_sar.vh_over_vv.to_masked_array()
#         thirdmask = stacked_vh_vv.mask
#     except AttributeError:
#         thirdmask = np.zeros(np.shape(stacked_vv.mask))
    
#     maskclusters = ma.empty(np.shape(stacked_vv))
    
#     #if the output is not empty, otherwise the empty masked_array is fine anyway
#     if len(output) > 0:
#         maskclusters[np.logical_and(~stacked_vv.mask,~stacked_vh.mask,~thirdmask)] = output
#         maskclusters.mask = ~np.logical_and(~stacked_vv.mask,~stacked_vh.mask,~thirdmask)

#     #same coords as the original stacked DataArray
#     coords = stacked_sar['z']

#     cluster_xr = xr.DataArray(maskclusters, coords={'z':coords},dims=['z'])

#     return cluster_xr.unstack().transpose('y','x')

