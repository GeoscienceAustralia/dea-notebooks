
import xarray as xr
import numpy as np
from datacube.helpers import write_geotiff

mask_dir = 'data/nmdb_LSandOEH_mask_clean.tif'
comm_mask = 'data/commission_mask.tif'

mask = xr.open_rasterio(mask_dir).squeeze()
comm = xr.open_rasterio(comm_mask).squeeze()

#combine LSandOEH mask with commission mask
combined_mask = xr.DataArray(np.where((comm==0) & (mask==1), 1, 0),
                             coords=[comm.y,comm.x],
                             dims=['y', 'x'],
                             name='combined_mask',
                             attrs=comm.attrs)

combined_mask = combined_mask.to_dataset()
combined_mask = combined_mask.astype('int16')
combined_mask.attrs = comm.attrs

write_geotiff('data/nmdb_LSandOEH_mask_commission_cleaned.tif', mask_clean)