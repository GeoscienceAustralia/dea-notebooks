import datacube
import xarray as xr
from datacube.helpers import ga_pq_fuser
from datacube.storage import masking
import fiona
from datacube.utils import geometry

from math import ceil
dc = datacube.Datacube()
import os
import sys
from datacube.drivers.netcdf import write_dataset_to_netcdf



output_dir = '/g/data/r78/vmn547/delwp/output2'
shape_file = '/g/data/r78/vmn547/delwp/SHPs_CKrause/GW_CATCHMENTS.shp'

args = sys.argv[1].split(',')
part = args[0]
part = int(part)

print(f'Working on chunk {part}')

numChunks = args[1]
numChunks = int(numChunks)
print(f'Splitting into {numChunks} chunks')

shp_name = shape_file.split('/')[-1].split('.')[0].replace(' ', '_')
with fiona.open(shape_file) as shapes:
    crs = geometry.CRS(shapes.crs_wkt)
    ShapesList = list(shapes)
    ChunkSize = ceil(len(ShapesList) / numChunks) + 1
    shapessubset = shapes[(part - 1) * ChunkSize: part * ChunkSize]


product = 'nbart'


from datetime import datetime

for shape in shapessubset:
    first_geometry = shape['geometry']
    shp_id = shape['properties']['OBJECTID']

    # Set up query
    geom = geometry.Geometry(first_geometry, crs=crs)
    current_time = datetime.now()
    time_period = ('1987-01-01', current_time.strftime('%m/%d/%Y'))
    query = {'geopolygon': geom, 'time': time_period}

    xarray_dict = {}
    for sensor in ['ls5', 'ls7', 'ls8']:

        # Load data 
        landsat_ds = dc.load(product=f'{sensor}_{product}_albers',
                             group_by='solar_day',
                             **query)

        if len(landsat_ds.attrs) > 0:
            # Load PQ data
            landsat_pq = dc.load(product=f'{sensor}_pq_albers',
                                 measurements=['pixelquality'],
                                 group_by='solar_day',
                                 **query)

            # Filter to subset of Landsat observations that have matching PQ data
            time = (landsat_ds.time - landsat_pq.time).time
            landsat_ds = landsat_ds.sel(time=time)
            landsat_pq = landsat_pq.sel(time=time)

            # Create PQ mask
            good_quality = masking.make_mask(landsat_pq.pixelquality,
                                             cloud_acca='no_cloud',
                                             cloud_shadow_acca='no_cloud_shadow',
                                             cloud_shadow_fmask='no_cloud_shadow',
                                             cloud_fmask='no_cloud',
                                             blue_saturated=False,
                                             green_saturated=False,
                                             red_saturated=False,
                                             nir_saturated=False,
                                             swir1_saturated=False,
                                             swir2_saturated=False,
                                             contiguous=True)

            # Apply mask to set all PQ-affected pixels to NaN and set nodata to NaN
            landsat_ds = landsat_ds.where(good_quality)

            # Add result to dict
            xarray_dict[sensor] = landsat_ds
        # fname = os.path.join(output_dir, f'{product}/collection2/c2_{sensor}_{product}_albers_2012_01_2019_02.nc')
        # write_dataset_to_netcdf(landsat_ds,fname)
    # Concatenate multiple sensors into one dataset
    landsat_currentcollection = xr.concat(xarray_dict.values(), dim='time')
    landsat_currentcollection = landsat_currentcollection.sortby('time')
    fname = os.path.join(output_dir, f'c2_ls_{product}_albers_{shp_name}_{shp_id}_1987_2019.nc')
    write_dataset_to_netcdf(landsat_currentcollection, fname)

