## dea_classificationtools.py
'''
Description: This file contains a set of python functions for applying machine learning classifiying remote sensing data from Digital Earth Australia.

License: The code in this notebook is licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth Australia data is licensed under the Creative Commons by Attribution 4.0 license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

Compatibility: This script is compatible with the DEA VDI environment, but incompatible with the DEA Sandbox in its current (2019-09-26) default state. This is because it requires scikit-learn to be installed, which is not the case
               by default on the sandbox. The workaround is to run `pip install --user scikit-learn' in a terminal on the sandbox, but this may break functionality if a conflicting version of scikit-learn is installed on the sandbox
               in the future.

If you would like to report an issue with this script, you can file one on Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: September 2019

Authors: Richard Taylor, Sean Chua, ...

'''

import numpy as np
import xarray as xr

from sklearn.cluster import KMeans

#'Wrappers' to translate xarrays to np arrays and back for interfacing with sklearn models

def sklearn_flatten(input_xr):
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

def sklearn_unflatten(output_np,input_xr):
    
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
    

    
def fit_xr(model,input_xr):
    """
    Utilise our wrappers to fit a vanilla sklearn model.
    
    Last modified: September 2019
    
    Parameters
    ----------  
        model : a scikit-learn model or compatible object. Must have a fit() method that takes
                numpy arrays.
        input_xr : a DataArray or Dataset. Must have dimensions 'x' and 'y', may have dimension 'time'.
                   
    Returns
    ----------
        model : a scikit-learn model which has been fitted to the data in the pixels of input_xr.
    
    """
    
    model = model.fit(sklearn_flatten(input_xr))
    return model

def predict_xr(model,input_xr):
    """
    Utilise our wrappers to predict with a vanilla sklearn model.
    
    Last modified: September 2019
    
    Parameters
    ----------  
        model : a scikit-learn model or compatible object. Must have a predict() method that takes
                numpy arrays.
        input_xr : a DataArray or Dataset. Must have dimensions 'x' and 'y', may have dimension 'time'.
                   
    Returns
    ----------
        output_xr : a DataArray containing the prediction output from model with input_xr as input. Has
        the same spatiotemporal structure as input_xr.
    
    """
    
    output_np = model.predict(sklearn_flatten(input_xr))
    output_xr = sklearn_unflatten(output_np,input_xr)
    
    return output_xr

def make_supervised_data(input_xr,labelled_polys):
    """
    Turn an input xarray and some labelled polygons into a training/testing dataset of pixels for a supervised
    classification model.
    
    Last modified: September 2019
    
    Parameters
    ----------  
        input_xr : a DataArray or Dataset. Must have dimensions 'x' and 'y', may have dimension 'time'.
        training_polys : 
                   
    Returns
    ----------
    
    """
    pass

class KMeans_tree():
    """
    A hierarchical KMeans unsupervised clustering model. This class is designed to be compatible with methods and kwargs from
    the sklearn.cluster.KMeans() class
    """
    pass