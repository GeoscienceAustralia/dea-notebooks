from datacube.virtual import construct_from_yaml
from datacube import Datacube
from datacube.drivers.netcdf import create_netcdf_storage_unit, write_dataset_to_netcdf
from dask.distributed import LocalCluster, Client
cluster = LocalCluster()
client = Client(cluster)
dc = Datacube(env='c3-samples')

query = {'time':('1987-12-01', '2011-02-28'),
        'x': (-1740000, -1670000),
        'y': (-2160000, -2230000),
        'crs': 'EPSG:3577'
    }

tci = construct_from_yaml("""
        aggregate: datacube_stats.aggregation.NewGeomedianStatistic
        num_threads: 1
        group_by: year
        input:
            reproject:
              output_crs: EPSG:3577
              resolution: [-30, 30]
              resampling: average
            input:
                transform: apply_mask
                mask_measurement_name: fmask
                dilation: 3
                input:
                  transform: expressions
                  output: 
                    fmask:
                      formula: (fmask != 2) & (fmask != 3) & (fmask != 0) & (oa_nbart_contiguity == 1)
                      nodata: False 
                    nbart_red: nbart_red
                    nbart_green: nbart_green
                    nbart_blue: nbart_blue
                    nbart_nir: nbart_nir
                    nbart_swir_1: nbart_swir_1
                    nbart_swir_2: nbart_swir_2
                  input:
                    product: ga_ls8c_ard_3
                    measurements: [nbart_red, nbart_green, nbart_blue, nbart_nir, nbart_swir_1, nbart_swir_2, fmask, oa_nbart_contiguity]
                    gqa_iterative_mean_xy: [0, 1]
                """)
datasets = tci.query(dc, **query)
grouped = tci.group(datasets, **query)
results = tci.fetch(grouped, **query, dask_chunks={'time':-1, 'x':800, 'y':800})
results.load()
write_dataset_to_netcdf(results, 'somefilenameifyouneed.nc')
