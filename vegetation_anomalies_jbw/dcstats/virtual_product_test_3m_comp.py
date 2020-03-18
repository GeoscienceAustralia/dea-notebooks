## Virtual Product creation to test C3 datacube stats

#Need to link to custom install of dc-stats and dc-core:
# export PYTHONPATH=/g/data/jbw156/cb3058/dea-notebooks/vegetation_anomalies/dc_refactor/datacube-stats/:$PYTHONPATH
# export PYTHONPATH=/g/data/r78/cb3058/dea-notebooks/vegetation_anomalies/dc_core/datacube-core/:$PYTHONPATH
# run in terminal
# export PYTHONPATH=/g/data/r78/jbw156/datacube-stats/:$PYTHONPATH
# export PYTHONPATH=/g/data/r78/jbw156/datacube-core/:$PYTHONPATH

from datacube.virtual import construct_from_yaml
from datacube import Datacube
from datacube.drivers.netcdf import create_netcdf_storage_unit, write_dataset_to_netcdf
from datacube.helpers import write_geotiff
from dask.distributed import LocalCluster, Client

#user inputs
lat, lon = -33.2, 149.1
buffer = 0.05
time = ('2019-02', '2019-04')

#set up query
dc = Datacube(env='c3-samples')

query = {'lon': (lon - buffer, lon + buffer),
         'lat': (lat - buffer, lat + buffer),
         'time': time}

#create VP from yaml
print('constructing from yaml')
ndvi_3m_comp = construct_from_yaml("""
        aggregate: datacube_stats.external.ndvi_3m_comp
        group_by: alltime
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
    """)

# load the VP and export
print('actually computing...')
datasets = ndvi_3m_comp.query(dc, **query)
print(datasets)
grouped = ndvi_3m_comp.group(datasets, **query)
print(grouped)
results = ndvi_3m_comp.fetch(grouped, **query, dask_chunks={'time':-1, 'x':250, 'y':250})
results.load()
# results=results.squeeze()
print(results)
print('writing to file')
write_dataset_to_netcdf(results, 'VP_test_NDVI_3mcomp_201902_201904.nc')
# write_geotiff('VP_test_NDVI_3mcomp_201902_201904.tif', results)
