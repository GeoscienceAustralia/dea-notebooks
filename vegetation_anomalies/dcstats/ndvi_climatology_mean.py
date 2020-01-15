import xarray
from datacube_stats.statistics import Statistic
from datacube_stats.statistics.uncategorized import PerBandIndexStat
from collections import Sequence
from datacube.model import Measurement
import numpy as np
import pandas as pd

class NDVI_climatology_mean(Statistic):
    """
    Calculate rolling quarterly NDVI mean climatolgies
    
    """
    def __init__(self, name, band1, band2):
        self.band1 = band1
        self.band2 = band2
        self.name = name
        
        quarter= {'JFM': [1,2,3],
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

    def compute(self, data, quarter):
        ndvi = xarray.Dataset(data_vars={'ndvi': (data.nir - data.red) / (data.nir + data.red)},
                              coords=data.coords,
                              attrs=dict(crs=data.crs))
        
        ndvi_var = []
        for q in quarter:
            ix=ndvi['time.month'].isin(quarter[q])
            ndvi_clim_mean=ndvi[ix].mean(dim='time')   
            ndvi_clim_mean=ndvi_clim_mean.rename('ndvi_clim_mean'+q)
            ndvi_var.append(ndvi_clim_mean)
            
        q_clim_mean = xr.merge(ndvi_var)   
        q_clim_mean.attrs = data.attrs    
            
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
        return [Measurement(name=m_name, dtype='float32', nodata=-1, units='1')
                for m_name in measurement_names]
