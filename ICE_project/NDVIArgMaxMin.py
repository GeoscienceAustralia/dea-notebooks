import xarray
from datacube_stats.statistics import Statistic
from datacube_stats.statistics.uncategorized import PerBandIndexStat
from collections import Sequence
from datacube.model import Measurement
import numpy as np
import pandas as pd

class NDVIArgMaxMin(Statistic):
    """
    Returns the argmax and argmin of an NDVI timeseries. Can handle all-NaN
    slices. Data is resampled to monthly means. The values returned correspond
    to the months of the year. 1=Jan, 12=Dec.
  
    Don't use this function if working with more than 12 months of data as the year 
    isn't returned.

    In the output GTiff the bands are:
    1: time of maximum NDVI
    2: time of minimum NDVI

    """

    def __init__(self, name, band1, band2):
        self.band1 = band1
        self.band2 = band2
        self.name = name

    def compute(self, data):
        ndvi = xarray.DataArray(data = (data[self.band1] - data[self.band2]) / (data[self.band1] + data[self.band2]),
                      coords=data.coords,attrs=dict(crs=data.crs))

        ndvi = ndvi.resample(time='M').mean('time')

        def returnMonthofStat(xarr, dim, stat):
            """
            Returns the month (an an integer;1-Jan, 12=Dec) of the argmax or
            argmin value.

            xarr= xarray dataArray, eg NDVI
            dim= dimension along which to calculate stats, usually 'time'
            stat= if 'max' then argmax, if 'min' then argmin
            """
            #generate a mask where entire axis along dimension is NaN
            mask = xarr.min(dim=dim, skipna=True).isnull()

            def allNaNarg(xarr, dim, stat):
                """
                Calculate nanargmax or nanargmin.
                Deals with all-NaN slices by filling those locations
                with an integer and then masking the offending cells.
                Value of the fillna() will never be returned as index of argmax/min
                as fill value exceeds the min/max value of the array.
                """
                if stat=='max':
                    y = xarr.fillna(float(xarr.min() - 1))
                    y = y.argmax(dim=dim, skipna=True).where(~mask)
                    return y
                if stat == 'min':
                    y = xarr.fillna(float(xarr.max() + 1))
                    y = y.argmin(dim=dim, skipna=True).where(~mask)
                    return y

            z = allNaNarg(xarr,dim = dim, stat=stat)

            #finding the unique values returned by argmax/min that aren't nans
            idx = np.unique(z)        
            idx = idx[~np.isnan(idx)]        

            #find the months in our dataset
            months = pd.DatetimeIndex(xarr.time.values).month.values 

            #replace the indices with the correct month
            for i, month in zip(idx, months):  
                z = z.where(z!=i, other=month)

            z=z.where(~mask) #get rid of the all-nan slices again

            return z
        
        timeofmax= returnMonthofStat(ndvi, dim='time', stat='max')
        timeofmin= returnMonthofStat(ndvi, dim='time', stat='min')
        
        results = xarray.Dataset(data_vars={'timeofmax': timeofmax,
                                            'timeofmin': timeofmin},
                                             attrs=dict(crs=data.crs))
        results.attrs['nodata'] = -9999
        results.attrs['units'] = 1

        return results 
    
    def measurements(self, input_measurements):
        measurement_names = ['timeofmax', 'timeofmin']
        return [Measurement(name=m_name, dtype='float32', nodata=-9999, units='1')
                for m_name in measurement_names]