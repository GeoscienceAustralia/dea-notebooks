#!/usr/bin/env python
# coding: utf-8

import glob
import xarray as xr
from affine import Affine
from rasterio.features import rasterize
from skimage.morphology import binary_opening
from skimage.morphology import binary_dilation
from skimage.morphology import disk, square
from skimage.measure import label
import numpy as np


def change_regress(row, 
                   x_vals, 
                   x_labels, 
                   std_dev=3, 
                   detrend_params=None,
                   slope_var='slope', 
                   interc_var='intercept',
                   pvalue_var='pvalue', 
                   outliers_var='outliers'):
    
    # Extract x (time) and y (distance) values
    x = x_vals
    y = row.values.astype(np.float)
    
    # Drop NAN rows
    xy_df = np.vstack([x, y]).T
    is_valid = ~np.isnan(xy_df).any(axis=1)
    xy_df = xy_df[is_valid]
    valid_labels = x_labels[is_valid]
    
    # If detrending parameters are provided, apply these to the data to
    # remove the trend prior to running the regression
    if detrend_params:
        xy_df[:,1] = xy_df[:,1]-(detrend_params[0]*xy_df[:,0]+detrend_params[1])    
    
    # Remove outliers
    outlier_bool = (np.abs(stats.zscore(xy_df)) < float(std_dev)).all(axis=1)
    xy_df = xy_df[outlier_bool]
        
    # Compute linear regression
    lin_reg = stats.linregress(x=xy_df[:,0], 
                               y=xy_df[:,1])  
       
    # Return slope, p-values and list of outlier years excluded from regression   
    return pd.Series({slope_var: np.round(lin_reg.slope, 3), 
                      interc_var: np.round(lin_reg.intercept, 3),
                      pvalue_var: np.round(lin_reg.pvalue, 3),
                      outliers_var: ' '.join(map(str, valid_labels[~outlier_bool]))})


def breakpoints(x, labels, model='rbf', pen=10, min_size=2, jump=1):
    '''
    Takes an array of erosion values, and returns a list of 
    breakpoint years
    '''
    signal = x.values
    algo = rpt.Pelt(model=model, min_size=min_size, jump=jump).fit(signal)
    result = algo.predict(pen=pen)
    if len(result) > 1:
        return [labels[i] for i in result[0:-1]][0]
    else:
        return None

    
def mask_ocean(bool_array, points_gdf, connectivity=1):
    '''
    Identifies ocean by selecting the largest connected area of water
    pixels, then dilating this region by 1 pixel to include mixed pixels
    '''
    
#     ocean_mask = largest_region(bool_array, connectivity=connectivity)
    # First, break boolean array into unique, discrete regions/blobs
    blobs_labels = xr.apply_ufunc(label, bool_array, None, 0, False, connectivity)
    
    # Get blob ID for each tidal modelling point
    x = xr.DataArray(points_gdf.geometry.x, dims='z')
    y = xr.DataArray(points_gdf.geometry.y, dims='z')   
    ocean_blobs = np.unique(blobs_labels.interp(x=x, y=y, method='nearest'))

    # Return only blobs that contained tide modelling point
    ocean_mask = blobs_labels.isin(ocean_blobs[ocean_blobs != 0])
    
    # Dilate mask
    ocean_mask = binary_dilation(ocean_mask, selem=square(3))

    return ocean_mask


def rocky_shores_buffer(smartline_gdf, buffer=50):

    to_keep = (
               'Bedrock breakdown debris (cobbles/boulders)',
               'Boulder (rock) beach',
               'Cliff (>5m) (undiff)',
               'Colluvium (talus) undiff',
               'Flat boulder deposit (rock) undiff',
               'Hard bedrock shore',
               'Hard bedrock shore inferred',
               'Hard rock cliff (>5m)',
               'Hard rocky shore platform',
               'Rocky shore (undiff)',
               'Rocky shore platform (undiff)',
               'Sloping hard rock shore',
               'Sloping rocky shore (undiff)',
               'Soft `bedrock¿ cliff (>5m)',
               'Steep boulder talus',
               'Hard rocky shore platform'
    )

    # Extract rocky vs non-rocky
    rocky_gdf = smartline_gdf[smartline_gdf.INTERTD1_V.isin(to_keep)].copy()
    nonrocky_gdf = smartline_gdf[~smartline_gdf.INTERTD1_V.isin(to_keep)].copy()
    
    # Buffer both features
    rocky_gdf['geometry'] = rocky_gdf.buffer(buffer)
    nonrocky_gdf['geometry'] = nonrocky_gdf.buffer(buffer)
    
    return gpd.overlay(rocky_gdf, nonrocky_gdf, how='difference')


def load_rasters(output_name, 
                 study_area, 
                 water_index='mndwi'):

    # Get file paths
    gapfill_index_files = sorted(glob.glob(f'output_data/{output_name}_{study_area}/*_{water_index}_gapfill.tif'))
    gapfill_tide_files = sorted(glob.glob(f'output_data/{output_name}_{study_area}/*_tide_m_gapfill.tif'))
    gapfill_count_files = sorted(glob.glob(f'output_data/{output_name}_{study_area}/*_count_gapfill.tif'))
    index_files = sorted(glob.glob(f'output_data/{output_name}_{study_area}/*_{water_index}.tif'))[1:len(gapfill_index_files)+1]
    stdev_files = sorted(glob.glob(f'output_data/{output_name}_{study_area}/*_stdev.tif'))[1:len(gapfill_index_files)+1]
    tidem_files = sorted(glob.glob(f'output_data/{output_name}_{study_area}/*_tide_m.tif'))[1:len(gapfill_index_files)+1]
    count_files = sorted(glob.glob(f'output_data/{output_name}_{study_area}/*_count.tif'))[1:len(gapfill_index_files)+1]

    # Create variable used for time axis
    time_var = xr.Variable('year', [int(i.split('/')[2][0:4]) for i in index_files])

    # Import data
    index_da = xr.concat([xr.open_rasterio(i) for i in index_files], dim=time_var)
    gapfill_index_da = xr.concat([xr.open_rasterio(i) for i in gapfill_index_files], dim=time_var)
    gapfill_tide_da = xr.concat([xr.open_rasterio(i) for i in gapfill_tide_files], dim=time_var)
    gapfill_count_da = xr.concat([xr.open_rasterio(i) for i in gapfill_count_files], dim=time_var)
    stdev_da = xr.concat([xr.open_rasterio(i) for i in stdev_files], dim=time_var)
    tidem_da = xr.concat([xr.open_rasterio(i) for i in tidem_files], dim=time_var)
    count_da = xr.concat([xr.open_rasterio(i) for i in count_files], dim=time_var)

    # Assign names to allow merge
    index_da.name = water_index
    gapfill_index_da.name = 'gapfill_index'
    gapfill_tide_da.name = 'gapfill_tide_m'
    gapfill_count_da.name = 'gapfill_count'
    stdev_da.name = 'stdev'
    tidem_da.name = 'tide_m'
    count_da.name = 'count'

    # Combine into a single dataset and set CRS
    yearly_ds = xr.merge([index_da, gapfill_index_da, gapfill_tide_da, 
                          gapfill_count_da, stdev_da, tidem_da, count_da]).squeeze('band', drop=True)
    yearly_ds.attrs['crs'] = index_da.crs
    yearly_ds.attrs['transform'] = Affine(*index_da.transform)

    return yearly_ds


def contours_preprocess(yearly_ds, 
                        water_index, 
                        index_threshold, 
                        estuary_gdf, 
                        points_gdf):

    # Remove low obs and high variance pixels and replace with 3-year gapfill
    gapfill_mask = (yearly_ds['count'] > 5) # & (yearly_ds['stdev'] < 0.5)
    yearly_ds[water_index] = yearly_ds[water_index].where(gapfill_mask, other=yearly_ds.gapfill_index)
    yearly_ds['tide_m'] = yearly_ds['tide_m'].where(gapfill_mask, other=yearly_ds.gapfill_tide_m)

    # Apply water index threshold
    thresholded_ds = (yearly_ds[water_index] > index_threshold)
    thresholded_ds = thresholded_ds.where(~yearly_ds[water_index].isnull())

    # Rasterize estuary polygons into a numpy mask. The try-except catches cases
    # where no estuary polygons exist in the study area
    try:
        estuary_mask = rasterize(shapes=estuary_gdf['geometry'],
                                 out_shape=yearly_ds[water_index].shape[1:],
                                 transform=yearly_ds.transform,
                                 all_touched=True).astype(bool)
    except:
        estuary_mask = np.full(yearly_ds[water_index].shape[1:], False, dtype=bool)

    # Drop empty timesteps and apply estuary mask
    thresholded_ds = (thresholded_ds
                      .sel(year=thresholded_ds.sum(dim=['x', 'y']) > 0)
                      .where(~estuary_mask, 0))

    # Identify ocean by identifying the largest connected area of water pixels
    # as water in at least 90% of the entire stack of thresholded data
    all_time_median = (thresholded_ds.mean(dim='year') > 0.9)
    full_sea_mask = mask_ocean(xr.apply_ufunc(binary_opening, 
                                              all_time_median, 
                                              disk(3)), points_gdf)

    # Generate all time 750 m buffer from ocean-land boundary
    buffer_ocean = binary_dilation(full_sea_mask, disk(25))
    buffer_land = binary_dilation(~full_sea_mask, disk(25))
    coastal_buffer = buffer_ocean & buffer_land

    # # Generate sea mask for each timestep
    yearly_sea_mask = (thresholded_ds.groupby('year')
                       .apply(lambda x: mask_ocean(x, points_gdf)))

    # Keep only pixels that are within 750 m of the ocean in the
    # full stack, and directly connected to ocean in each yearly timestep
    masked_ds = yearly_ds[water_index].where(yearly_sea_mask & coastal_buffer)

    # Set CRS and trasnform from input data
    masked_ds.attrs['crs'] = yearly_ds.crs[6:]
    masked_ds.attrs['transform'] = yearly_ds.transform

    return masked_ds
    
def main(argv=None):

    if argv is None:

        argv = sys.argv
        print(sys.argv)

    # If no user arguments provided
    if len(argv) < 3:

        str_usage = "You must specify a study area ID and name"
        print(str_usage)
        sys.exit()
        
    # Set study area and name for analysis
    study_area = int(argv[1])
    output_name = str(argv[2])
    

        
if __name__ == "__main__":
    main()