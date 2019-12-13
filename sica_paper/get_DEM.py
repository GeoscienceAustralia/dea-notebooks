import numpy as np
import xarray as xr
import datacube
from datacube.utils import geometry
from datacube.utils.geometry import CRS
from datacube.helpers import write_geotiff
import fiona
import rasterio.mask
import rasterio.features

shp_path = "../data/northern_basins.shp"
dc = datacube.Datacube(app='get_dem')

with fiona.open(shp_path) as input:
    crs = geometry.CRS(input.crs_wkt)

feat = fiona.open(shp_path)[0]

first_geom = feat['geometry']
geom = geometry.Geometry(first_geom, crs=crs) 

# Create the 'query' dictionary object
query = {'geopolygon': geom,
    'output_crs': 'EPSG:3577',
    'resolution': (-25, 25),
#     'dask_chunks': {'x':1000, 'y':1000}
}
print('getting data')
dsm = dc.load(product='dsm1sv10', **query)

# using plygon to mask extracted rainfall data
mask = rasterio.features.geometry_mask([geom.to_crs(dsm.geobox.crs)for geoms in [geom]],
                                               out_shape=dsm.geobox.shape,
                                               transform=dsm.geobox.affine,
                                               all_touched=False,
                                               invert=False)

print('masking')
mask_xr = xr.DataArray(mask, dims = ('y','x'))
dsm= dsm.where(mask_xr==False)
dsm = dsm.squeeze()

# Write geotiff to a location
print('exporting geotiff')
write_geotiff('../data/nmdb_DEM.tif', dsm)


