import xarray
from datacube_stats.statistics import Statistic
from datacube_stats.statistics.uncategorized import PerBandIndexStat
from collections import Sequence
from datacube.model import Measurement
import numpy as np
import pandas as pd

class MSAVI_SeasonalAnomalies(Statistic):
    """
    Modified soil adjusted vegetation index (MSAVI) anomalies.
    Use Band 1 = red, and Band 2 = NIR in the yaml
    """
    def __init__(self, name, band1, band2):
        self.band1 = band1
        self.band2 = band2
        self.name = name

    def compute(self, data):		
        #calculate the MSAVI
        msavi = xarray.DataArray(data = (2*data[self.band2]+1-np.sqrt((2*data[self.band2]+1)**2 - 8*(data[self.band2]-data[self.band1])))/2,
                      coords=data.coords,attrs=dict(crs=data.crs))
        #resample to monthly means
        msavi = msavi.resample(time='M').mean('time')
        #calculate seasonal climatology
        msavi_seasonalClimatology = msavi.groupby('time.season').mean('time')
        #resample monthly msavi to seasonal means
        msavi_seasonalMeans = msavi.resample(time='QS-DEC').mean('time')
        #calculate anomalies
        masvi_anomalies = msavi_seasonalMeans.groupby('time.season') - msavi_seasonalClimatology

        #build dataset to return result
        results = xarray.Dataset(data_vars={'msavi_anomalies': masvi_anomalies},
                                             attrs=dict(crs=data.crs))
        results.attrs['nodata'] = -9999
        results.attrs['units'] = 1

        return results 

    def measurements(self, input_measurements):
        measurement_names = ['msavi_anomalies']
        return [Measurement(name=m_name, dtype='float32', nodata=-9999, units='1')
                for m_name in measurement_names]