## Virtual Product creation to test C3 datacube stats

#Need to link to custom install of dc-stats:
# export PYTHONPATH=/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/dc_refactor/datacube-stats/:$PYTHONPATH

from datacube.virtual import construct_from_yaml
from datacube import Datacube
from datacube.drivers.netcdf import create_netcdf_storage_unit, write_dataset_to_netcdf
from dask.distributed import LocalCluster, Client

# #Create dask cluster
# client = locals().get('client', None)
# if client is not None:
#     client.close()
#     del client

# cluster = LocalCluster()
# client = Client(cluster)
    
#user inputs
lat, lon = -33.2, 149.1
buffer = 0.15
time = ('1992', '2008')

#set up query
dc = Datacube(app='test_VP_ndvi_clim')
query = {'lon': (lon - buffer, lon + buffer),
         'lat': (lat - buffer, lat + buffer),
         'time': time,
         'measurements':['nbart_red', 'nbart_red'],
         'crs': 'EPSG:3577'
    }

#create VP from yaml
print('constructing from yaml')
ndvi_clim_mean = construct_from_yaml("""
        aggregate: datacube_stats.external.ndvi_clim_mean
        group_by: year
        input:
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
                        formula: (fmask != 2) & (fmask != 3) & (fmask != 0) & (oa_nbart_contiguity == 1)
                        nodata: False
                    nbart_red: nbart_red
                    nbart_nir: nbart_nir
                  input:
                    product: ga_ls8c_ard_3
                    measurements: [nbart_red, nbart_nir, fmask, oa_nbart_contiguity]
                    gqa_iterative_mean_xy: [0, 1]
                    dataset_predicate: datacube_stats.main.ls8_on
              - transform: apply_mask
                mask_measurement_name: fmask
                dilation: 3
                input:
                  transform: expressions
                  output: 
                    fmask:
                        formula: (fmask != 2) & (fmask != 3) & (fmask != 0) & (oa_nbart_contiguity == 1)
                        nodata: False
                    nbart_red: nbart_red
                    nbart_nir: nbart_nir
                  input:
                    product: ga_ls7c_ard_3
                    measurements: [nbart_red, nbart_nir, fmask, oa_nbart_contiguity]
                    gqa_iterative_mean_xy: [0, 1]
                    dataset_predicate: datacube_stats.main.ls7_on
              - transform: apply_mask
                mask_measurement_name: fmask
                dilation: 3
                input:
                  transform: expressions
                  output: 
                    fmask:
                        formula: (fmask != 2) & (fmask != 3) & (fmask != 0) & (oa_nbart_contiguity == 1)
                        nodata: False
                    nbart_red: nbart_red
                    nbart_nir: nbart_nir
                  input:
                    product: ga_ls5c_ard_3
                    measurements: [nbart_red, nbart_nir,fmask, oa_nbart_contiguity]
                    gqa_iterative_mean_xy: [0, 1]
                    dataset_predicate: datacube_stats.main.ls5_on
    """)

#load the VP and export
print('actually computing...')
datasets = ndvi_clim_mean.query(dc, **query)
grouped = ndvi_clim_mean.group(datasets, **query)
results = ndvi_clim_mean.fetch(grouped, **query, dask_chunks={'time':-1, 'x':250, 'y':250})
results.load()

print('writing to file')
write_dataset_to_netcdf(results, 'VP_test_NDVI_climatology.nc')