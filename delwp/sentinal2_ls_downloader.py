import datacube
import xarray as xr
import fiona
from datacube.utils import geometry

dc = datacube.Datacube()
import os

from datacube.drivers.netcdf import write_dataset_to_netcdf

output_dir = '/g/data/r78/vmn547/delwp/output_s2'
shape_file = '/g/data/r78/vmn547/delwp/SHPs_CKrause/GHCMA_Lower G3_region.shp'
shp_name = shape_file.split('/')[-1].split('.')[0].replace(' ', '_')
with fiona.open(shape_file) as shapes:
    crs = geometry.CRS(shapes.crs_wkt)
    shapes_list = list(shapes)


# Desired output resolution and projection for both s2 products
mask =False
output_resolution = (-10, 10)
output_resamp_continuous = 'bilinear'
output_resamp_categorical = 'nearest'
output_crs = 'EPSG:3577'
_bands = ['nbar_contiguity','nbar_coastal_aerosol','nbar_red', 'nbar_green', 'nbar_blue', 'nbar_red_edge_1',
          'nbar_red_edge_2', 'nbar_red_edge_3','nbar_nir_1', 'nbar_nir_2',
                                   'nbar_swir_2', 'nbar_swir_3', 'fmask']

from datetime import datetime

for shape in shapes_list:
    first_geometry = shape['geometry']
    shp_id = shape['properties']['ID']

    # Set up query
    geom = geometry.Geometry(first_geometry, crs=crs)
    current_time = datetime.now()
    time_period = ('2019-01-01', current_time.strftime('%m/%d/%Y'))
    query = {'geopolygon': geom, 'time': time_period}

    xarray_dict = {}
    for sensor in ['s2a', 's2b']:
        # Load data
        s2_ds = dc.load(product=f'{sensor}_ard_granule',
                        measurements=_bands,
                        output_crs=output_crs,
                        resolution=output_resolution,
                        resampling=output_resamp_continuous,
                        group_by='solar_day',
                        **query)
        if mask:
            # Load PQ data seperately (this enables using a different resampling method on
            # continuous surface reflectance values vs categorical fmask/PQ values)
            s2_pq = dc.load(product=f'{sensor}_ard_granule',
                                     measurements=['fmask'],
                                     output_crs=output_crs,
                                     resolution=output_resolution,
                                     resampling=output_resamp_categorical,
                                     group_by='solar_day',
                                     **query)

            # Identify pixels with valid data: no nodata AND no cloud AND no cloud shadow
            good_quality = ((s2_pq.fmask != 0) &
                            (s2_pq.fmask != 2) &
                            (s2_pq.fmask != 3))

            # Apply mask to set all PQ-affected pixels to NaN and set nodata to NaN
            s2_ds = s2_ds.where(good_quality)

        # Add result to dict
        xarray_dict[sensor] = s2_ds
        #uncomment if you want to write out s2a and s2b separately
    #   fname = os.path.join(output_dir, f'{sensor}_albers_{shp_name}_{shp_id}_2016_01_2019_03.nc')
    #   write_dataset_to_netcdf(s2_ds,fname)

    # Concatenate multiple sensors into one dataset
    s2 = xr.concat(xarray_dict.values(), dim='time')
    s2 = s2.sortby('time')
    fname = os.path.join(output_dir, f's2a_s2b_albers_{shp_name}_{shp_id}_2016_01_2019_05.nc')
    write_dataset_to_netcdf(s2, fname)

