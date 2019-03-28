import xarray
from datacube_stats.statistics import Statistic
from datacube_stats.statistics.uncategorized import PerBandIndexStat
from collections import Sequence
from datacube.model import Measurement
import numpy as np
import pandas as pd

class rate_of_change(Statistic):
    """
       Returning the rate of change of NDVI, after resampling the 
       time series to monthly means. Also returns the time of minimum
       and time of maximum NDVI.
       
       In the output GTiff the bands are:
       1=rate of change from the minimum NDVi to the peak NDVI (NDVI/month)
       2=time of maximum NDVI (month- as an integer where 0 is
                               the first month of the input timeseries)
       3=time of minimum NDVI
       
       """

    def __init__(self, name, band1, band2):
        self.band1 = band1
        self.band2 = band2
        self.name = name

    def compute(self, data):
        ndvi = xarray.DataArray(data = (data[self.band1] - data[self.band2]) / (data[self.band1] + data[self.band2]),
                      coords=data.coords,attrs=dict(crs=data.crs))

        ndvi = ndvi.resample(time='M').mean('time')

        ndvi_max = ndvi.max('time')
        ndvi_min = ndvi.min('time')

        def nanarg(xarr, dim, stat):
            """
            deals with all-NaN slices by filling those locations
            with an integer and then masking the offending cells
            after computing nanargmin(max)
            """
            #generate a mask where entire all values along a dimension are NaN
            mask = xarr.min(dim=dim, skipna=True).isnull()
            if stat=='max':
                y = xarr.fillna(-99.0)
                y = y.argmax(dim=dim, skipna=True).astype(float)
                y = y.where(~mask)
                return y
            if stat == 'min':
                y = xarr.fillna(100)
                y = y.argmin(dim=dim, skipna=True).astype(float)
                y = y.where(~mask)
                return y
        
        
        timeofmax = nanarg(ndvi,dim ='time', stat='max')
        timeofmin = nanarg(ndvi,dim ='time', stat='min')

        rate = (ndvi_max-ndvi_min)/(timeofmax - timeofmin)
        rate = rate.where(~np.isnan(rate<=3), other=3) #remove any unreasonable values
        
        results = xarray.Dataset(data_vars={'rate':rate,
                                        'timeofmax': timeofmax,
                                        'timeofmin': timeofmin},
                                        attrs=dict(crs=data.crs))
        results.attrs['nodata'] = -9999
        results.attrs['units'] = 1

        return results 
    
    def measurements(self, input_measurements):
        measurement_names = ['rate', 'timeofmax', 'timeofmin']
        return [Measurement(name=m_name, dtype='float32', nodata=-9999, units='1')
                for m_name in measurement_names]