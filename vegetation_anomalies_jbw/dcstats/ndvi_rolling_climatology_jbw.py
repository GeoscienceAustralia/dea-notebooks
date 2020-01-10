import xarray
from datacube_stats.statistics import Statistic
from datacube_stats.statistics.uncategorized import PerBandIndexStat
from collections import Sequence
from datacube.model import Measurement
import numpy as np
import pandas as pd

class ndvi_rolling_climatology_jbw(Statistic):
    """
    NDVI climatology.
    Will calculate long term mean for each season but only return
    a single season, of your choosing (because dcstats doesn't return
    mulitple time-steps)
    Use Band 1 = red, and Band 2 = NIR in the yaml
    """
    def __init__(self, name, band1, band2):
        self.band1 = band1
        self.band2 = band2
        self.name = name

    def compute(self, data):		
        #Scale reflectance values to 0-1
        red = data[self.band1] / 10000
        nir = data[self.band2] / 10000
        
#         msavi = (2*nir+1-((2*nir+1)**2 - 8*(nir-red))**0.5)/2
        ndvi=(nir-red)/(nir+red)
        ndvi = ndvi.astype('float32') #convert to reduce memory
    
        #calculate climatologies
        msavi = msavi.resample(time='QS-DEC').mean('time')
        climatology_mean = msavi.groupby('time.season').mean('time')
        djf = climatology_mean.sel(season='DJF')
                                                                               
        #build dataset to return result
        results = xarray.Dataset(data_vars={'msavi_DJF_mean_climatology': djf},
                                             attrs=dict(crs=data.crs))                                                                            
        results.attrs['nodata'] = -9999
        results.attrs['units'] = 1
                                                                               
        return results 

    def measurements(self, input_measurements):
        measurement_names = ['msavi_DJF_mean_climatology']
        return [Measurement(name=m_name, dtype='float32', nodata=-9999, units='1')
                for m_name in measurement_names]