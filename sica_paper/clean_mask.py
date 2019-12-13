#Use a DEM to clean commission errors in the irrigable area mask

import xarray as xr
import geopandas as gpd
import shapely
import rasterio.features
import numpy as np
from datacube.helpers import write_geotiff

elevation_threshold = 650
mask_shapefile = 'data/nmdb_LSandOEH_mask_dirty.shp'
dem_tif = 'data/nmdb_DEM.tif'

#open dataset
dem = xr.open_rasterio(dem_tif).squeeze()

# grab spatial info for later
transform = dem.transform
y, x = dem.values.shape
ycoords, xcoords = dem.y, dem.x
attrs = dem.attrs
crs = dem.crs

#threshold the elevation model 
print('thresholding DEM')
dem = dem < elevation_threshold

#convert mask polygons into raster
print('rasterizing mask')
mask = gpd.read_file(mask_shapefile)
shapes = zip(mask['geometry'], mask['DN'])
mask_raster = rasterio.features.rasterize(shapes=shapes,
                                         out_shape=(y, x),
                                         all_touched=False,
                                         fill=np.nan,
                                         transform=transform)

# Convert result to a xarray.DataArray
mask_raster = xr.DataArray(mask_raster,
                                  coords=[ycoords, xcoords],
                                  dims=['y', 'x'],
                                  name='clean_mask',
                                  attrs=attrs)

# and mask with DEM
print('cleaning mask')
mask_clean = mask_raster.where(dem)
mask_clean = xr.DataArray(np.where(np.isfinite(mask_clean.values), 1, 0),
                                  coords=[ycoords, xcoords],
                                  dims=['y', 'x'],
                                  name='clean_mask',
                                  attrs=attrs)

#export
print('exporting geotiff')
# Convert to xarray dataset to assist with writing to GeoTIFF
mask_clean = mask_clean.to_dataset()
mask_clean = mask_clean.astype('int16') #write geotiff needs this
mask_clean.attrs = attrs

write_geotiff('data/nmdb_LSandOEH_mask_clean.tif', mask_clean)


