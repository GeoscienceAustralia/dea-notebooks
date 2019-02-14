import numpy as np
import xarray
from datacube_stats.statistics import Statistic
from datacube.model import Measurement

class radarwofs(Statistic):
    zeroish = 0.0001

    def measurements(self, input_measurements):
        names = [m.name for m in input_measurements]
        assert 'vv' in names
        assert 'vh' in names
        clear = Measurement(name='clear_count', dtype='int16', nodata=-1, units='1')
        wet = Measurement(name='wet_count', dtype='int16', nodata=-1, units='1')
        summary = Measurement(name='wet_freq', dtype='float32', nodata=np.nan, units='1')
        return [clear, wet, summary]

    def compute(self, data):
        # apply classification logic
        singledim = data.vv + data.vh
        wet = singledim < 0.008
        dry = singledim > 0.1

        # prevent misclassifying spurious input
        nodata = (data.vv < self.zeroish) & (data.vh < self.zeroish) 
        wet.values[nodata.values] = 0

        #unsure = ~wet & ~dry
        #clear = wet | dry
        
        wets = wet.sum(dim='time')
        clears = wets + dry.sum(dim='time')
        freq = wets / clears

        return xarray.Dataset({'wet_count':wets, 'clear_count':clears, 'wet_freq':freq},
                              attrs={'crs': data.crs})




        
