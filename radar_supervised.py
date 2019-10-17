"""Testing supervised decision tree methods for a possible SAR wetlands insight tool.

Richard Taylor, 2019
"""


from sklearn import tree
import radar_gmm as rg
import numpy as np
import xarray as xr

#maintain consistency of the shape of underlying data arrays
dim_order = ['x','y','time']


def flatten_ds(dataset):
    """
    convert xarray dataset or dataarray into a flat array for input into the decision tree methods
    """
    
    try:
        stacked = dataset.transpose(*dim_order).stack(z=dim_order)
        masked_flat_ds = stacked.to_masked_array()
        valid = masked_flat_ds[~masked_flat_ds.mask]
    except:
        stacked = dataset.transpose(*dim_order).stack(z=dim_order)
        masked_flat_ds = stacked.to_array().to_masked_array()
        valid = (masked_flat_ds.T)[~(masked_flat_ds.mask.any(axis=0))]
        
    return valid

def train_tree(radar_ds,WIT_ds,**kwargs):
    """Returns a trained decision tree given the three-component SAR dataset and the wetlands insight tool maps over time.
    """
    
    radar_ds = radar_ds.sortby('x',ascending=True)
    radar_ds = radar_ds.sortby('y',ascending=True)
    radar_ds = radar_ds.sortby('time',ascending=True)
    
    
    WIT_ds = WIT_ds.sortby('x',ascending=True)
    WIT_ds = WIT_ds.sortby('y',ascending=True)
    WIT_ds = WIT_ds.sortby('time',ascending=True)
    
    tree_model = tree.DecisionTreeClassifier(**kwargs)
    
    #pick up the nearest neighbour radar scenes for each wetlands insight scene
    #(the radar is way denser and more consistent so this will work better than the opposite way)
    radar_train_ds = radar_ds.reindex(time=WIT_ds.time,method='nearest',tolerance=np.timedelta64(5,'D'))
    
    #make the nan masks the same
    radar_train_ds = radar_train_ds.where(~np.isnan(WIT_ds))
    WIT_ds = WIT_ds.where(~np.isnan(radar_train_ds.to_array()).any(dim='variable'))
    
    features,labels = (flatten_ds(radar_train_ds),flatten_ds(WIT_ds).astype(int))
    
    tree_model = tree_model.fit(features,labels)
    
    return tree_model

def rebuild_ds(output_arr,input_ds):
    """
    Turn a numpy array back into a dataarray with the same shape and masks as input_ds.
    """
    input_mask = input_ds.sortby('y',ascending=True).transpose(*dim_order).stack(z=dim_order).to_array().to_masked_array().mask.any(axis=0)
    masked_output = np.ma.empty(np.shape(input_mask))
    masked_output.mask = input_mask
    
    masked_output.data[~masked_output.mask] = output_arr
    
    coords = input_ds.stack(z=dim_order)['z']
    
    output_xr = xr.DataArray(masked_output, coords={'z':coords},dims=['z'])
    return output_xr.unstack()

