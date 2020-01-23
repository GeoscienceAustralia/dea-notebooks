## Virtual Product creation to test C3 datacube stats

#Need to link to custom install of dc-stats and dc-core:
# export PYTHONPATH=/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/dc_refactor/datacube-stats/:$PYTHONPATH
# export PYTHONPATH=/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/dc_core/datacube-core/:$PYTHONPATH

from datacube.virtual import construct_from_yaml
from datacube import Datacube
from datacube.drivers.netcdf import create_netcdf_storage_unit, write_dataset_to_netcdf
from dask.distributed import LocalCluster, Client
import numpy as np
import xarray as xr

#user inputs
lat, lon = -33.2, 149.1
buffer = 0.05
time = ('1987', '2010')

#set up query
dc = Datacube(env='c3-samples')

query = {'lon': (lon - buffer, lon + buffer),
         'lat': (lat - buffer, lat + buffer),
         'time': time}

#create VP from yaml
# datacube_stats.external.ndvi_clim_mean
print('constructing from yaml')
ndvi_clim_mean = construct_from_yaml("""
          reproject:
            output_crs: EPSG:3577
            resolution: [-30, 30]
            resampling: average
          input:
            collate:
              - transform: apply_mask
                mask_measurement_name: fmask
                dilation: 3
                input:
                  transform: expressions
                  output: 
                    fmask:
                        formula: (fmask != 2) & (fmask != 3) & (fmask != 0)
                        nodata: False
                    nbart_red: nbart_red
                    nbart_nir: nbart_nir
                  input:
                    product: ga_ls7e_ard_3
                    measurements: [nbart_red, nbart_nir, fmask]
                    gqa_iterative_mean_xy: [0, 1]
                    dataset_predicate: datacube_stats.main.ls7_on
              - transform: apply_mask
                mask_measurement_name: fmask
                dilation: 3
                input:
                  transform: expressions
                  output: 
                    fmask:
                        formula: (fmask != 2) & (fmask != 3) & (fmask != 0)
                        nodata: False
                    nbart_red: nbart_red
                    nbart_nir: nbart_nir
                  input:
                    product: ga_ls5t_ard_3
                    measurements: [nbart_red, nbart_nir,fmask]
                    gqa_iterative_mean_xy: [0, 1]
                    dataset_predicate: datacube_stats.main.ls5_on
    """)

#load the VP and export
print('actually computing...')
datasets = ndvi_clim_mean.query(dc, **query)
print(datasets)
grouped = ndvi_clim_mean.group(datasets, **query)
results = ndvi_clim_mean.fetch(grouped, **query, dask_chunks={'time':-1, 'x':100, 'y':100})
results.load()

print(results)

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

def ndvi_clim_mean(data):
#     print(data)
    def attrs_reassign(da, dtype=np.float32):
        da_attr = data.attrs
        da = da.assign_attrs(**da_attr)
        return da
    
    ndvi = xr.Dataset(data_vars={'ndvi': (data.nbart_nir - data.nbart_red) / (data.nbart_nir + data.nbart_red)},
                          coords=data.coords,
                          attrs=dict(crs=data.crs))
#     print(ndvi)
    ndvi_var = []
    for q in quarter:
        ix=ndvi['time.month'].isin(quarter[q])
        ndvi_clim_mean=ndvi.where(ix,drop = True).mean(dim='time')   
        ndvi_clim_mean=ndvi_clim_mean.to_array(name='ndvi_clim_mean_'+q).drop('variable').squeeze()
        ndvi_var.append(ndvi_clim_mean)

    q_clim_mean = xr.merge(ndvi_var)   

    #assign back attributes
    q_clim_mean.attrs = data.attrs 
    q_clim_mean = q_clim_mean.apply(attrs_reassign, keep_attrs=True)  

    return q_clim_mean

clim = ndvi_clim_mean(results)
print(clim)
print('writing to file')
write_dataset_to_netcdf(clim, 'mergeworkflows_test_1987_2010.nc')