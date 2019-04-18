# Tile netCDF and write out geotiff

from datacube.helpers import write_geotiff
from datacube.utils.geometry import CRS
import glob
import xarray as xr

# Read in the netCDF files created with datacube-stats
# Point to the folder where datacube-stats wrote out the tiles

statsoutputs = '/g/data/r78/cek156/datacube_stats/WOFSDams/*.nc'

# Open all the netCDF files and combine them into a single xarray
CombinedFiles = xr.merge([xr.open_dataset(f) for f in glob.glob(statsoutputs)])

# Remove any -1 no data values
CombinedFiles = CombinedFiles.where(CombinedFiles != -1)

# Write out our combined array wofs to GeoTiff

ds = CombinedFiles.to_dataset(name = 'frequency')
ds.attrs['transform'] = CombinedFiles.transform
ds.attrs['crs'] = CRS(CombinedFiles.crs)

write_geotiff('/g/data/r78/cek156/datacube_stats/WOFSDams/Combined.tif', ds.squeeze())

