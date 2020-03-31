#!/usr/bin/env python
# coding: utf-8

import glob
import xarray as xr
from affine import Affine
from rasterio.features import rasterize
from skimage.morphology import binary_opening
from skimage.morphology import binary_dilation, binary_erosion
from skimage.morphology import disk, square
from skimage.measure import label
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.ops import nearest_points
from datacube.helpers import write_geotiff
from scipy import stats

import os
import sys
from shapely.geometry import box
from rasterio.transform import array_bounds
import shutil

sys.path.append('../Scripts')
from dea_spatialtools import subpixel_contours


def outlier_mad(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False 
    otherwise.

    Parameters:
    -----------
    points : 
        An numobservations by numdimensions array of observations
    thresh : 
        The modified z-score to use as a threshold. Observations with a 
        modified z-score (based on the median absolute deviation) greater
        than this value will be classified as outliers.

    Returns:
    --------
    mask : 
        A numobservations-length boolean array.

    References:
    ----------
    Source: https://github.com/joferkington/oost_paper_code/blob/master/utilities.py
    
    Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
    Handle Outliers", The ASQC Basic References in Quality Control:
    Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 
    """
    if len(points.shape) == 1:
        points = points[:,None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    return modified_z_score > thresh


def change_regress(row, 
                   x_vals, 
                   x_labels, 
                   threshold=3.5, 
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
    outlier_bool = ~outlier_mad(xy_df, thresh=threshold)
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


def load_rasters(output_name, 
                 study_area, 
                 water_index='mndwi'):
    
    # Get file paths
    gapfill_index_files = sorted(glob.glob(f'output_data/{study_area}_{output_name}/*_{water_index}_gapfill.tif'))
    gapfill_tide_files = sorted(glob.glob(f'output_data/{study_area}_{output_name}/*_tide_m_gapfill.tif'))
    gapfill_count_files = sorted(glob.glob(f'output_data/{study_area}_{output_name}/*_count_gapfill.tif'))
    index_files = sorted(glob.glob(f'output_data/{study_area}_{output_name}/*_{water_index}.tif'))[1:len(gapfill_index_files)+1]
    stdev_files = sorted(glob.glob(f'output_data/{study_area}_{output_name}/*_stdev.tif'))[1:len(gapfill_index_files)+1]
    tidem_files = sorted(glob.glob(f'output_data/{study_area}_{output_name}/*_tide_m.tif'))[1:len(gapfill_index_files)+1]
    count_files = sorted(glob.glob(f'output_data/{study_area}_{output_name}/*_count.tif'))[1:len(gapfill_index_files)+1]

    # Test if data was returned
    if len(index_files) == 0:
        raise ValueError(f"No rasters found for grid cell {study_area} "
                         f"(analysis name '{output_name}'). Verify that "
                         f"`deacoastlines_generation.py` has been run "
                         "for this grid cell.")
    
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


def contours_preprocess_old(yearly_ds, 
                        water_index, 
                        index_threshold, 
                        estuary_gdf, 
                        points_gdf,
                        output_path):

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

    # Create raster containg all time mask data
    all_time_mask = np.full(yearly_ds[water_index].shape[1:], 0, dtype='int8')
    all_time_mask[buffer_land & ~coastal_buffer] = 1
    all_time_mask[buffer_ocean & ~coastal_buffer] = 2
    all_time_mask[estuary_mask & coastal_buffer] = 3
    
    # Export mask raster to assist evaluating results
    all_time_mask_da = xr.DataArray(data = all_time_mask, 
                                    coords={'x': yearly_ds.x, 
                                            'y': yearly_ds.y},
                                    dims=['y', 'x'],
                                    name='all_time_mask')
    all_time_mask_ds = all_time_mask_da.to_dataset()
    all_time_mask_ds.attrs = yearly_ds.attrs
    write_geotiff(filename=f'{output_path}/all_time_mask2.tif', 
                  dataset=all_time_mask_ds,
                  profile_override={'blockxsize': 1024, 
                                    'blockysize': 1024, 
                                    'compress': 'deflate', 
                                    'zlevel': 5})

    return masked_ds




def contours_preprocess(yearly_ds, 
                        water_index, 
                        index_threshold, 
                        estuary_gdf, 
                        points_gdf,
                        output_path):  
    
    # Rasterize estuary polygons into a numpy mask. The try-except catches cases
    # where no estuary polygons exist in the study area
    try:
        estuary_mask = rasterize(shapes=estuary_gdf['geometry'],
                                 out_shape=yearly_ds[water_index].shape[1:],
                                 transform=yearly_ds.transform,
                                 all_touched=True).astype(bool)
    except:
        estuary_mask = np.full(yearly_ds[water_index].shape[1:], False, dtype=bool)
    
    # Identify pixels with less than 5 annual observations or > 0.25 MNDWI 
    # standard deviation in at least 75 % of years. Apply erosion to 
    # focus on only large contiguous regions 
    quantile_ds = yearly_ds[['stdev', 'count']].quantile(q=0.75, dim='year')
    persistent_stdev = binary_erosion(image = quantile_ds['stdev'] > 0.25, 
                                      selem = disk(3)) 
    persistent_nodata = binary_erosion(image = quantile_ds['count'] < 5, 
                                       selem = disk(3)) 

    # Remove low obs pixels and replace with 3-year gapfill
    gapfill_mask = (yearly_ds['count'] > 5)
    yearly_ds[water_index] = yearly_ds[water_index].where(gapfill_mask, 
                                                          other=yearly_ds.gapfill_index)
    yearly_ds['tide_m'] = yearly_ds['tide_m'].where(gapfill_mask, 
                                                    other=yearly_ds.gapfill_tide_m)

    # Apply water index threshold
    thresholded_ds = ((yearly_ds[water_index] > index_threshold)
                      .where(~yearly_ds[water_index].isnull())
                      .where((~estuary_mask), 0))

    # Identify ocean by identifying the largest connected area of water pixels
    # as water in at least 90% of the entire stack of thresholded data
    all_time_median = (thresholded_ds.mean(dim='year') > 0.9)
    full_sea_mask = mask_ocean(xr.apply_ufunc(binary_opening, 
                                              all_time_median, 
                                              disk(3)), points_gdf)

    # Generate all time 1000 m buffer (~33 pixels) from ocean-land boundary
    buffer_ocean = binary_dilation(full_sea_mask, disk(33))
    buffer_land = binary_dilation(~full_sea_mask, disk(33))
    coastal_buffer = buffer_ocean & buffer_land

    # Generate sea mask for each timestep
    yearly_sea_mask = (thresholded_ds
                       .groupby('year')
                       .apply(lambda x: mask_ocean(x, points_gdf)))

    # Keep only pixels that are within 1000 m of the ocean in the
    # full stack, and directly connected to ocean in each yearly timestep
    masked_ds = yearly_ds[water_index].where((yearly_sea_mask & 
                                              coastal_buffer &
                                              ~persistent_stdev &
                                              ~persistent_nodata))
    masked_ds.attrs['crs'] = yearly_ds.crs[6:]
    masked_ds.attrs['transform'] = yearly_ds.transform    
    
    # Create raster containg all time mask data
    all_time_mask = np.full(yearly_ds[water_index].shape[1:], 0, dtype='int8')
    all_time_mask[buffer_land & ~coastal_buffer] = 1
    all_time_mask[buffer_ocean & ~coastal_buffer] = 2
    all_time_mask[estuary_mask & coastal_buffer] = 3
    all_time_mask[persistent_stdev & coastal_buffer] = 4
    all_time_mask[persistent_nodata & coastal_buffer] = 5
    
    # Export mask raster to assist evaluating results
    all_time_mask_da = xr.DataArray(data = all_time_mask, 
                                    coords={'x': yearly_ds.x, 
                                            'y': yearly_ds.y},
                                    dims=['y', 'x'],
                                    name='all_time_mask')
    all_time_mask_ds = all_time_mask_da.to_dataset()
    all_time_mask_ds.attrs = yearly_ds.attrs
    write_geotiff(filename=f'{output_path}/all_time_mask.tif', 
                  dataset=all_time_mask_ds,
                  profile_override={'blockxsize': 1024, 
                                    'blockysize': 1024, 
                                    'compress': 'deflate', 
                                    'zlevel': 5})

    return masked_ds


def stats_points(contours_gdf, baseline_year, distance=30):
    
    # Set annual shoreline to use as a baseline
    baseline_contour = contours_gdf.loc[[baseline_year]].geometry

    # Generate points along line and convert to geopandas.GeoDataFrame
    points_line = [baseline_contour.iloc[0].interpolate(i) 
                   for i in range(0, int(baseline_contour.length), distance)]
    points_gdf = gpd.GeoDataFrame(geometry=points_line, crs=contours_gdf.crs)
    
    return points_gdf


def rocky_shores_clip(points_gdf, smartline_gdf, buffer=50):

    rocky = [
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
    ]
    
    # Identify rocky features
    rocky_bool = (smartline_gdf.INTERTD1_V.isin(rocky) & 
                  smartline_gdf.INTERTD2_V.isin(rocky + ['Unclassified']))

    # Extract rocky vs non-rocky
    rocky_gdf = smartline_gdf[rocky_bool].copy()
    nonrocky_gdf = smartline_gdf[~rocky_bool].copy()

    # If both rocky and non-rocky shorelines exist, clip points to remove
    # rocky shorelines from the stats dataset
    if (len(rocky_gdf) > 0) & (len(nonrocky_gdf) > 0):

        # Buffer both features
        rocky_gdf['geometry'] = rocky_gdf.buffer(buffer)
        nonrocky_gdf['geometry'] = nonrocky_gdf.buffer(buffer)
        rocky_shore_buffer = (gpd.overlay(rocky_gdf, 
                                          nonrocky_gdf, 
                                          how='difference')
                              .geometry
                              .unary_union)
        
        # Keep only non-rocky shore features and reset index         
        points_gdf = points_gdf[~points_gdf.intersects(rocky_shore_buffer)]        
        points_gdf = points_gdf.reset_index(drop=True)        
        
        return points_gdf

    # If no rocky shorelines exist, return the points data as-is
    elif len(nonrocky_gdf) > 0:          
        return points_gdf
   
    # If no sandy shorelines exist, return nothing
    else:
        return None


def annual_movements(yearly_ds, 
                     points_gdf, 
                     tide_points_gdf, 
                     contours_gdf, 
                     baseline_year, 
                     water_index):

    # Get array of water index values for baseline time period 
    baseline_array = yearly_ds[water_index].sel(year=int(baseline_year))

    # Copy baseline point geometry to new column in points dataset
    points_gdf['p_baseline'] = points_gdf.geometry
    baseline_x_vals = points_gdf.geometry.x
    baseline_y_vals = points_gdf.geometry.y

    # Years to analyse
    years = contours_gdf.index.unique().values

    # Iterate through all comparison years in contour gdf
    for comp_year in years:

        print(comp_year, end='\r')

        # Set comparison contour
        comp_contour = contours_gdf.loc[[comp_year]].geometry.iloc[0]

        # Find nearest point on comparison contour, and add these to points dataset
        points_gdf[f'p_{comp_year}'] = points_gdf.apply(lambda x: 
                                                        nearest_points(x.p_baseline, 
                                                                       comp_contour)[1], 
                                                        axis=1)

        # Compute distance between baseline and comparison year points and add
        # this distance as a new field named by the current year being analysed
        points_gdf[f'{comp_year}'] = points_gdf.apply(lambda x: 
                                                      x.geometry.distance(x[f'p_{comp_year}']), 
                                                      axis=1)

        # Extract comparison array containing water index values for the 
        # current year being analysed
        comp_array = yearly_ds[water_index].sel(year=int(comp_year))

        # Convert baseline and comparison year points to geoseries to allow 
        # easy access to x and y coords
        comp_x_vals = gpd.GeoSeries(points_gdf[f'p_{comp_year}']).x
        comp_y_vals = gpd.GeoSeries(points_gdf[f'p_{comp_year}']).y

        # Sample water index values from arrays for baseline and comparison points
        baseline_x_vals = xr.DataArray(baseline_x_vals, dims='z')
        baseline_y_vals = xr.DataArray(baseline_y_vals, dims='z')
        comp_x_vals = xr.DataArray(comp_x_vals, dims='z')
        comp_y_vals = xr.DataArray(comp_y_vals, dims='z')   
        points_gdf['index_comp_p1'] = comp_array.interp(x=baseline_x_vals, 
                                                        y=baseline_y_vals)
        points_gdf['index_baseline_p2'] = baseline_array.interp(x=comp_x_vals, 
                                                                y=comp_y_vals)

        # Compute change directionality (negative = erosion, positive = accretion)    
        points_gdf['loss_gain'] = np.where(points_gdf.index_baseline_p2 > 
                                           points_gdf.index_comp_p1, 1, -1)
        points_gdf[f'{comp_year}'] = (points_gdf[f'{comp_year}'] * 
                                      points_gdf.loss_gain)

        # Add tide data
        tide_array = yearly_ds['tide_m'].sel(year=int(comp_year))
        tide_points_gdf[f'{comp_year}'] = tide_array.interp(x=baseline_x_vals, 
                                                            y=baseline_y_vals)

    # Keep required columns
    points_gdf = points_gdf[['geometry'] + years.tolist()]
    points_gdf = points_gdf.round(2)

    # Zero values to 1988
    points_gdf.iloc[:,1:] = points_gdf.iloc[:, 1:].subtract(points_gdf['1988'], axis=0)
    
    return points_gdf, tide_points_gdf


def calculate_regressions(yearly_ds, 
                          points_gdf, 
                          tide_points_gdf, 
                          climate_df):

    # Restrict climate and points data to years in datasets
    x_years = yearly_ds.year.values
    points_subset = points_gdf[x_years.astype(str)]
    tide_subset = tide_points_gdf[x_years.astype(str)]
    climate_subset = climate_df.loc[x_years, :]

    # Compute coastal change rates by linearly regressing annual movements vs. time
    print(f'Comparing annual movements with time')
    rate_out = (points_subset
                .apply(lambda x: change_regress(row=x,
                                                x_vals=x_years,
                                                x_labels=x_years), axis=1))
    points_gdf[['rate_time', 'incpt_time', 'sig_time', 'outl_time']] = rate_out

    # Compute whether coastal change estimates are influenced by tide by linearly
    # regressing residual tide heights against annual movements. A significant 
    # relationship indicates that it may be difficult to isolate true erosion/
    # accretion from the influence of tide
    print(f'Comparing annual movements with tide heights')
    tide_out = (tide_subset
                .apply(lambda x: change_regress(row=points_subset.iloc[x.name],
                                                x_vals=x, 
                                                x_labels=x_years), axis=1))
    points_gdf[['rate_tide', 'incpt_tide', 'sig_tide', 'outl_tide']] = tide_out 

    # Identify possible relationships between climate indices and coastal change 
    # by linearly regressing climate indices against annual movements. Significant 
    # results indicate that annual movements may be influenced by climate phenomena
    for ci in climate_subset:

        print(f'Comparing annual movements with {ci}')

        # Compute stats for each row
        ci_out = (points_subset
                  .apply(lambda x: change_regress(row=x, 
                                                  x_vals=climate_subset[ci].values, 
                                                  x_labels=x_years), axis=1))

        # Add data as columns  
        points_gdf[[f'rate_{ci}', f'incpt_{ci}', f'sig_{ci}', f'outl_{ci}']] = ci_out

    # Set CRS
    points_gdf.crs = yearly_ds.crs

    # Custom sorting
    column_order = [
        'rate_time', 'rate_SOI', 'rate_IOD', 'rate_SAM', 'rate_IPO', 'rate_PDO',
        'rate_tide', 'sig_time', 'sig_SOI', 'sig_IOD', 'sig_SAM', 'sig_IPO',
        'sig_PDO', 'sig_tide', 'outl_time', 'outl_SOI', 'outl_IOD', 'outl_SAM',
        'outl_IPO', 'outl_PDO', 'outl_tide', *x_years.astype(str).tolist(),
        'geometry'
    ]

    return points_gdf.loc[:, column_order]

    
def main(argv=None):
    
    #########
    # Setup #
    #########

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
        
    # Set params
    water_index = 'mndwi'
    index_threshold = 0.00
    baseline_year = '2018'

    # Create output vector folder
    output_dir = f'output_data/{study_area}_{output_name}/vectors'
    os.makedirs(f'{output_dir}/shapefiles', exist_ok=True)

    ###############################
    # Load DEA CoastLines rasters #
    ###############################
    
    yearly_ds = load_rasters(output_name, study_area, water_index)

    ######################
    # Load external data #
    ######################

    # Get bounding box to load data for
    bbox = gpd.GeoSeries(box(*array_bounds(height=yearly_ds.sizes['y'], 
                                           width=yearly_ds.sizes['x'], 
                                           transform=yearly_ds.transform)), 
                         crs=yearly_ds.crs)

    # Estaury mask
    estuary_gdf = (gpd.read_file('input_data/SurfaceHydrologyPolygonsRegional.gdb', bbox=bbox)
                   .to_crs(yearly_ds.crs))
    to_keep = estuary_gdf.FEATURETYPE.isin(['Foreshore Flat', 
                                            'Land Subject To Inundation', 
                                            'Saline Coastal Flat', 
                                            'Marine Swamp'])
    estuary_gdf = estuary_gdf[~to_keep]

    # Rocky shore mask
    smartline_gdf = (gpd.read_file('input_data/Smartline.gdb', bbox=bbox)
                     .to_crs(yearly_ds.crs))

    # Tide points
    points_gdf = (gpd.read_file('input_data/tide_points_coastal.geojson', bbox=bbox)
                  .to_crs(yearly_ds.crs))

    # Study area polygon
    comp_gdf = (gpd.read_file('input_data/50km_albers_grid.shp', bbox=bbox)
                .set_index('id')
                .to_crs(str(yearly_ds.crs)))

    # Mask to study area
    study_area_poly = comp_gdf.loc[study_area]

    # Load climate indices
    climate_df = pd.read_csv('input_data/climate_indices.csv', index_col='year')

    ##############################
    # Extract shoreline contours #
    ##############################

    # Mask dataset to focus on coastal zone only
    masked_ds = contours_preprocess(yearly_ds, 
                                    water_index, 
                                    index_threshold, 
                                    estuary_gdf, 
                                    points_gdf,
                                    output_path=f'output_data/{study_area}_{output_name}')

    # Extract contours
    contours_gdf = subpixel_contours(da=masked_ds,
                                     z_values=index_threshold,
                                     min_vertices=10,
                                     dim='year').set_index('year')

    ######################
    # Compute statistics #
    ######################    
    
    # Extract statistics modelling points along baseline contour
    points_gdf = stats_points(contours_gdf, baseline_year, distance=30)
    
    # Clip to remove rocky shoreline points
    points_gdf = rocky_shores_clip(points_gdf, smartline_gdf, buffer=50)
    
    # If any points remain after rocky shoreline clip
    if points_gdf is not None:

        # Make a copy of the points GeoDataFrame to hold tidal data
        tide_points_gdf = points_gdf.copy()

        # Calculate annual coastline movements and residual tide heights 
        # for every contour compared to the baseline year
        points_gdf, tide_points_gdf = annual_movements(yearly_ds, 
                                                       points_gdf, 
                                                       tide_points_gdf, 
                                                       contours_gdf, 
                                                       baseline_year,
                                                       water_index)

        # Calculate regressions
        points_gdf = calculate_regressions(yearly_ds, 
                                           points_gdf, 
                                           tide_points_gdf, 
                                           climate_df)

        ################
        # Export stats #
        ################

        # Clip stats to study area extent, remove rocky shores
        stats_path = f'{output_dir}/stats_{study_area}_{output_name}_' \
                     f'{water_index}_{index_threshold:.2f}'
        points_gdf = points_gdf[points_gdf.intersects(study_area_poly['geometry'])]

        # Export to GeoJSON
        points_gdf.to_file(f'{stats_path}.geojson', driver='GeoJSON')

        # Export as ESRI shapefiles
        stats_path = stats_path.replace('vectors', 'vectors/shapefiles')
        points_gdf.to_file(f'{stats_path}.shp')
    
    ###################
    # Export contours #
    ###################    
    
    # Clip annual shoreline contours to study area extent
    contour_path = f'{output_dir}/contours_{study_area}_{output_name}_' \
                   f'{water_index}_{index_threshold:.2f}'
    contours_gdf['geometry'] = contours_gdf.intersection(study_area_poly['geometry'])
    contours_gdf.reset_index().to_file(f'{contour_path}.geojson', driver='GeoJSON')

    # Export stats and contours as ESRI shapefiles
    contour_path = contour_path.replace('vectors', 'vectors/shapefiles')
    contours_gdf.to_file(f'{contour_path}.shp')
    
    #######
    # Zip #
    #######
    
    # Create a zip file containing all vector files
    shutil.make_archive(base_name=f'output_data/outputs_{study_area}_{output_name}', 
                        format='zip', 
                        root_dir=output_dir)


if __name__ == "__main__":
    main()