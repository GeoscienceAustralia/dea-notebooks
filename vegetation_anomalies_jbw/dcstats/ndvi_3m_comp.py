import xarray
from datacube.model import Measurement
from datacube.virtual.impl import Transformation
import numpy as np
import pandas as pd


class ndvi_3m_comp(Transformation):
    """
    Calculate NDVI composite for past 3 months 

    """

    def __init__(self):

        self.quarter_dict = {1: 'JFM',
                         2: 'FMA',
                         3: 'MAM',
                         4: 'AMJ',
                         5: 'MJJ',
                         6: 'JJA',
                         7: 'JAS',
                         8: 'ASO',
                         9: 'SON',
                         10: 'OND',
                         11: 'NDJ',
                         12: 'DJF',
                         }

    def compute(self, data):
        def attrs_reassign(da, dtype=np.float32):
            da_attr = data.attrs
            da = da.assign_attrs(**da_attr)
        return da

        ndvi = xr.Dataset(data_vars={'ndvi': (data.nbart_nir - data.nbart_red) / (data.nbart_nir + data.nbart_red)},
                      coords=data.coords,
                      attrs=dict(crs=data.crs))

        FirstMonth = ndvi['time.month'].min().values.tolist()         
        Year=ndvi['time.year'].min().values.tolist()
        Q3M = self.quarter_dict[FirstMonth]
        self.measurement_name=str(Year)+'_'+str(Q3M)+'_ndvi_mean'

        ndvi_mean = ndvi.mean(dim='time')

        # add back metadata
        ndvi_mean = ndvi_mean.to_array(name=self.measurement_name)
        ndvi_mean.attrs = data.attrs
#         ndvi_mean = ndvi_mean.apply(attrs_reassign, keep_attrs=True)

        return ndvi_mean

    def measurements(self, input_measurements):       
       
        measurement_names=[self.measurement_name]
        
        return [Measurement(name=m_name, dtype='float32', nodata=-9999, units='1')
                for m_name in measurement_names]
