
import xarray
from datacube.model import Measurement
from datacube.virtual.impl import Transformation
import numpy as np
import pandas as pd

class NDVI_climatology_mean(Transformation):
    """
    Calculate rolling quarterly NDVI mean climatolgies
    
    """
    def __init__(self):
    
        self.quarter= {'JFM': [1,2,3],
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

    def compute(self, data, self.quarter):
        
        def attrs_reassign(da, dtype=np.float32):
        """little function to reassigna atributes
        to the dataArrays inside a dataset"""
            da_attr = data.attrs
            da = da.assign_attrs(**da_attr)
            return da

        ndvi = xarray.Dataset(data_vars={'ndvi': (data.nbart_nir - data.nbart_red) / (data.nbart_nir + data.nbart_red)},
                              coords=data.coords,
                              attrs=dict(crs=data.crs))
        
        ndvi_var = []
        for q in self.quarter:
            ix=ndvi['time.month'].isin(self.quarter[q])
            ndvi_clim_mean=ndvi[ix].mean(dim='time')   
            ndvi_clim_mean=ndvi_clim_mean.rename('ndvi_clim_mean'+q)
            ndvi_var.append(ndvi_clim_mean)
            
        q_clim_mean = xr.merge(ndvi_var)   
        #assign back attributes
        q_clim_mean.attrs = data.attrs 
        q_clim_mean = q_clim_mean.apply(attrs_reassign, keep_attrs=True)  
            
        return q_clim_mean

    def measurements(self, input_measurements):
        measurement_names = [
            'JFM',
            'FMA',
            'MAM',
            'AMJ',
            'MJJ',
            'JJA',
            'JAS',
            'ASO',
            'SON',
            'OND',
            'NDJ',
            'DJF']
       
        output_measurements = dict()
        for m_name in measurement_names:
            output_measurements[m_name] = Measurement(name=m_name, dtype='float32', nodata=-999, units='1')
        
        return output_measurements
