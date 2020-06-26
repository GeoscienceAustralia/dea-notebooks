#!/usr/bin/env python
# coding: utf-8

import math
import glob
import re
import os.path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from pathlib import Path
from io import StringIO
from pyproj import Transformer
from itertools import takewhile
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from shapely.geometry import box, Point, LineString


def dms2dd(s):
    # example: s = "0°51'56.29"
    degrees, minutes, seconds = re.split('[°\'"]+', s)
    if float(degrees) > 0:
        dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    else:
        dd = float(degrees) - float(minutes) / 60 - float(seconds) / (60 * 60);
    return dd


def dist_angle(lon, lat, dist, angle):
    lon_end = lon + dist *  np.sin(angle * np.pi / 180)
    lat_end = lat + dist *  np.cos(angle * np.pi / 180)
    return pd.Series({'end_y': lat_end, 'end_x': lon_end})


def interp_intercept(x, y1, y2, reverse=False):
    """Find the intercept of two curves, given by the same x data"""
    
    def intercept(point1, point2, point3, point4):
        """find the intersection between two lines
        the first line is defined by the line between point1 and point2
        the first line is defined by the line between point3 and point4
        each point is an (x,y) tuple.

        So, for example, you can find the intersection between
        intercept((0,0), (1,1), (0,1), (1,0)) = (0.5, 0.5)

        Returns: the intercept, in (x,y) format
        """    

        def line(p1, p2):
            A = (p1[1] - p2[1])
            B = (p2[0] - p1[0])
            C = (p1[0] * p2[1] - p2[0] * p1[1])
            return A, B, -C

        def intersection(L1, L2):
            D  = L1[0] * L2[1] - L1[1] * L2[0]
            Dx = L1[2] * L2[1] - L1[1] * L2[2]
            Dy = L1[0] * L2[2] - L1[2] * L2[0]

            x = Dx / D
            y = Dy / D
            return x,y

        L1 = line([point1[0],point1[1]], [point2[0],point2[1]])
        L2 = line([point3[0],point3[1]], [point4[0],point4[1]])

        R = intersection(L1, L2)

        return R

    try:

        if isinstance(y2, (int, float)):

            y2 = np.array([y2] * len(x))

        if reverse:

            x = x[::-1]
            y1 = y1[::-1]
            y2 = y2[::-1]

        idx = np.argwhere(np.diff(np.sign(y1 - y2)) != 0)
        xc, yc = intercept((x[idx], y1[idx]),((x[idx + 1], y1[idx + 1])), 
                           ((x[idx], y2[idx])), ((x[idx + 1], y2[idx + 1])))

        return xc[0][0]
    
    except: 
        
        return np.nan
    
    
def dist_along_transect(dist, start_x, start_y, end_x, end_y):    
 
    transect_line = LineString([(start_x, start_y), (end_x, end_y)])
    distance_coords = transect_line.interpolate(dist).coords.xy
    return [coord[0] for coord in distance_coords]


def waterline_intercept(x, 
                        dist_col='distance', 
                        x_col='x', 
                        y_col='y', 
                        z_col='z', 
                        z_val=0): 
    
    # Extract distance and coordinates of where the z_val first 
    # intersects with the profile line
    dist_int = interp_intercept(x[dist_col].values, x[z_col].values, z_val)
    x_int = interp_intercept(x[x_col].values, x[z_col].values, z_val)
    y_int = interp_intercept(x[y_col].values, x[z_col].values, z_val)
    
    # Identify last distance where the z_value intersects the profile
    rev_int = interp_intercept(x[dist_col].values, x[z_col].values, z_val, 
                               reverse=True)
    
    # If first and last intersects are the identical, return data. 
    # If not, the comparison is invalid (i.e. NaN)
    if dist_int == rev_int:
        return pd.Series({f'{z_val}_dist': dist_int, 
                          f'{z_val}_x': x_int, 
                          f'{z_val}_y': y_int})
    else:
        return pd.Series({f'{z_val}_dist': np.NaN, 
                          f'{z_val}_x': np.NaN, 
                          f'{z_val}_y': np.NaN})
    

def detect_misaligned_points(profiles_df, x='x', y='y', threshold=10):

    survey_points = gpd.points_from_xy(profiles_df[x], profiles_df[y])
    transect_lines = profiles_df.apply(
        lambda x: LineString([(x.start_x, x.start_y), 
                              (x.end_x, x.end_y)]).buffer(threshold), axis=1)
    
    return [t.contains(s) for t, s in zip(transect_lines, survey_points)]


def reproj_crs(in_data, 
               in_crs, 
               x='x', 
               y='y', 
               out_crs='EPSG:3577'):

    # Reset index to allow merging new data with original data
    in_data = in_data.reset_index(drop=True)

    # Reproject coords to Albers and create geodataframe
    trans = Transformer.from_crs(in_crs, out_crs, always_xy=True) 
    coords = trans.transform(in_data[x].values, in_data[y].values)
    in_data[['x', 'y']] = pd.DataFrame(zip(*coords))

    return in_data


def profiles_from_dist(profiles_df, 
                       id_col='id', 
                       dist_col='distance', 
                       x_col='x', 
                       y_col='y'):
    
    # Compute origin points for each profile
    min_ids = profiles_df.groupby(id_col)[dist_col].idxmin()
    start_xy = profiles_df.loc[min_ids, [id_col, x_col, y_col]]
    start_xy = start_xy.rename({x_col: f'start_{x_col}', 
                                y_col: f'start_{y_col}'}, 
                               axis=1)
    
    # Compute end points for each profile
    max_ids = profiles_df.groupby(id_col)[dist_col].idxmax()
    end_xy = profiles_df.loc[max_ids, [x_col, y_col]]
    
    # Add end coords into same dataframe
    start_xy = start_xy.reset_index(drop=True)
    end_xy = end_xy.reset_index(drop=True)
    start_xy[[f'end_{x_col}', f'end_{y_col}']] = end_xy
    
    return start_xy


def perpendicular_line(input_line, length):

    # Generate parallel lines either side of input line
    left = input_line.parallel_offset(length / 2.0, 'left')
    right = input_line.parallel_offset(length / 2.0, 'right')
    
    # Create new line between centroids of parallel line.
    # This should be perpendicular to the original line
    return LineString([left.centroid, right.centroid])


def generate_transects(line_geom,
                       length=400,
                       interval=200, 
                       buffer=20):
    
    # Create tangent line at equal intervals along line geom
    interval_dists = np.arange(buffer, line_geom.length, interval)
    tangent_geom = [LineString([line_geom.interpolate(dist - buffer), 
                                line_geom.interpolate(dist + buffer)]) 
                    for dist in interval_dists]

    # Convert to geoseries and remove erroneous lines by length
    tangent_gs = gpd.GeoSeries(tangent_geom)
    tangent_gs = tangent_gs.loc[tangent_gs.length.round(1) <= buffer * 2]

    # Compute perpendicular lines
    return tangent_gs.apply(perpendicular_line, length=length)


def coastal_transects(bbox, 
                      interval=200,
                      transect_length=400,
                      simplify_length=200,
                      output_crs='EPSG:3577',
                      coastline='../input_data/Smartline.gdb',
                      land_poly='/g/data/r78/rt1527/shapefiles/australia/australia/cstauscd_r.shp'):

    # Load smartline
    coastline_gdf = gpd.read_file(coastline, bbox=bbox).to_crs(output_crs)
    coastline_geom = coastline_gdf.geometry.unary_union.simplify(simplify_length)

    # Load Australian land water polygon
    land_gdf = gpd.read_file(land_poly, bbox=bbox).to_crs('EPSG:3577')
    land_gdf = land_gdf.loc[land_gdf.FEAT_CODE.isin(["mainland", "island"])]
    land_geom = gpd.overlay(df1=land_gdf, df2=bbox).unary_union

    # Extract transects along line
    geoms = generate_transects(coastline_geom,
                               length=transect_length,
                               interval=interval)

    # Test if end points of transects fall in water or land
    p1 = gpd.GeoSeries([Point(i.coords[0]) for i in geoms])
    p2 = gpd.GeoSeries([Point(i.coords[1]) for i in geoms])
    p1_within_land = p1.within(land_geom)
    p2_within_land = p2.within(land_geom)

    # Create geodataframe, remove invalid land-land/water-water transects 
    transect_gdf = gpd.GeoDataFrame(data={'p1': p1_within_land, 
                                          'p2': p2_within_land}, 
                                    geometry=geoms.values, 
                                    crs=output_crs)
    transect_gdf = transect_gdf[~(transect_gdf.p1 == transect_gdf.p2)]

    # Reverse transects so all point away from land
    transect_gdf['geometry'] = transect_gdf.apply(
        lambda i: LineString([i.geometry.coords[1], 
                              i.geometry.coords[0]]) 
        if i.p1 < i.p2 else i.geometry, axis=1) 
    
    return transect_gdf


def preprocess_wadot(regions_gdf,
                     fname='input_data/wadot/Coastline_Movements_20190819.gdb',
                     smartline='../input_data/Smartline.gdb',
                     aus_poly='/g/data/r78/rt1527/shapefiles/australia/australia/cstauscd_r.shp'):
    
    # Iterate through all features in regions gdf
    for i, _ in regions_gdf.iterrows():

        # Extract compartment as a GeoDataFrame so it can be used to clip other data
        compartment = regions_gdf.loc[[i]]
        beach = str(i).replace(' ', '').replace('/', '').lower()
        print(f'Processing {beach:<80}', end='\r')

        # Read file and filter to AHD 0 shorelines
        val_gdf = gpd.read_file(fname, 
                                bbox=compartment).to_crs('EPSG:3577')
        val_gdf = val_gdf[(val_gdf.TYPE == 'AHD 0m') | 
                          (val_gdf.TYPE == 'AHD 0m ')]

        # Filter to post 1987 shorelines and set index to year
        val_gdf = val_gdf[val_gdf.PHOTO_YEAR > 1987]
        val_gdf = val_gdf.set_index('PHOTO_YEAR')

        # If no data is returned, skip this iteration
        if len(val_gdf.index) == 0:
            print(f'Failed: {beach:<80}', end='\r')
            continue

        ######################
        # Generate transects #
        ######################

        transect_gdf = coastal_transects(bbox=compartment)
        transect_gdf['profile'] = list(map(str, range(0, len(transect_gdf.index))))

        ################################
        # Identify 0 MSL intersections #
        ################################

        output_list = []

        # Select one year
        for year in val_gdf.index.unique().sort_values(): 

            # Extract validation contour
            print(f'Processing {beach} {year:<80}', end='\r')
            val_contour = val_gdf.loc[[year]].geometry.unary_union

            # Copy transect data, and find intersects 
            # between transects and contour
            intersect_gdf = transect_gdf.copy()
            intersect_gdf['val_point'] = transect_gdf.intersection(val_contour)
            to_keep = gpd.GeoSeries(intersect_gdf['val_point']).geom_type == 'Point'
            intersect_gdf = intersect_gdf.loc[to_keep]

            # If no data is returned, skip this iteration
            if len(intersect_gdf.index) == 0:
                print(f'Failed: {beach} {year:<80}', end='\r')
                continue

            # Add generic metadata
            intersect_gdf['date'] = pd.to_datetime(str(year))
            intersect_gdf['beach'] = beach
            intersect_gdf['section'] = 'all'
            intersect_gdf['source'] = 'photogrammetry' 
            intersect_gdf['id'] = (intersect_gdf.beach + '_' + 
                                   intersect_gdf.section + '_' + 
                                   intersect_gdf.profile)
            
            # Add measurement metadata
            intersect_gdf[['start_x', 'start_y']] = intersect_gdf.apply(
                lambda x: pd.Series(x.geometry.coords[0]), axis=1)
            intersect_gdf[['end_x', 'end_y']] = intersect_gdf.apply(
                lambda x: pd.Series(x.geometry.coords[1]), axis=1)
            intersect_gdf['0_dist'] = intersect_gdf.apply(
                lambda x: Point(x.start_x, x.start_y).distance(x['val_point']), axis=1)
            intersect_gdf[['0_x', '0_y']] = intersect_gdf.apply(
                lambda x: pd.Series(x.val_point.coords[0]), axis=1)

            # Keep required columns
            intersect_gdf = intersect_gdf[['id', 'date', 'beach', 
                                           'section', 'profile',  
                                           'source', 'start_x', 
                                           'start_y', 'end_x', 'end_y', 
                                           '0_dist', '0_x', '0_y']]

            # Append to file
            output_list.append(intersect_gdf)

        # Combine all year data and export to file
        if len(output_list) > 0:
            shoreline_df = pd.concat(output_list)
            shoreline_df.to_csv(f'output_data/wadot_{beach:<80}.csv', index=False)

            
def preprocess_stirling(fname_out, datum=0):

    # List containing files to import and all params to extract data
    survey_xl = [
                 {'fname': 'input_data/stirling/2015 05 28 - From Stirling - Coastal Profiles 2014-2015 April-Feb with updated reef#2.xlsm',
                  'skiprows': 2,
                  'skipcols': 5,
                  'nrows': 100, 
                  'meta_skiprows': 0,
                  'meta_nrows': 1,
                  'meta_usecols': [6, 7]}, 
                 {'fname': 'input_data/stirling/Coastal Profiles 2013-2014 JUL-MAY#2.xlsx',
                  'skiprows': 2,
                  'skipcols': 5,
                  'nrows': 100, 
                  'meta_skiprows': 0,
                  'meta_nrows': 1,
                  'meta_usecols': [6, 7]}, 
                 {'fname': 'input_data/stirling/COASTAL PROFILES 2013 JAN - JUNE#2.xls',
                  'skiprows': 3,
                  'skipcols': 0,
                  'nrows': 40, 
                  'meta_skiprows': 1,
                  'meta_nrows': 2,
                  'meta_usecols': [1, 2]}, 
                 {'fname': 'input_data/stirling/COASTAL PROFILES 2012 JUN - DEC#2.xls',
                  'skiprows': 3,
                  'skipcols': 0,
                  'nrows': 40, 
                  'meta_skiprows': 1,
                  'meta_nrows': 2,
                  'meta_usecols': [1, 2]}, 
                 {'fname': 'input_data/stirling/COASTAL PROFILES 2011-2012 NOV - MAY#2.xls',
                  'skiprows': 3,
                  'skipcols': 0,
                  'nrows': 40, 
                  'meta_skiprows': 1,
                  'meta_nrows': 2,
                  'meta_usecols': [1, 2]}
                ]

    # List to contain processed profile data
    output = []

    # For each survey excel file in the list above:
    for survey in survey_xl:

        # Load profile start metadata
        all_meta = pd.read_excel(survey['fname'],
                                 sheet_name=None, 
                                 nrows=survey['meta_nrows'], 
                                 skiprows=survey['meta_skiprows'],
                                 usecols=survey['meta_usecols'], 
                                 header=None, 
                                 on_demand=True)

        # Load data
        all_sheets = pd.read_excel(survey['fname'],
                                   sheet_name=None, 
                                   skiprows=survey['skiprows'], 
                                   nrows=survey['nrows'], 
                                   parse_dates=False,
                                   usecols=lambda x: 'Unnamed' not in str(x))

        # Iterate through each profile in survey data
        for profile_id in np.arange(1, 20).astype('str'):

            # Extract profile start metadata and profile data    
            start_x, start_y = all_meta[profile_id].values[0]
            sheet = all_sheets[profile_id].iloc[:,survey['skipcols']:]

            # First set all column names to lower case strings
            sheet.columns = (sheet.columns.astype(str)
                             .str.slice(0, 10)
                             .str.lower())

            # Drop note columns and distance/angle offset
            sheet = sheet.loc[:,~sheet.columns.str.contains('note|notes')]
            sheet = sheet.drop(['dist', 'angle dd'], axis=1, errors='ignore')

            # Expand date column values into rows for each sampling event
            sheet.loc[:,sheet.columns[::4]] = sheet.columns[::4]

            # Number date columns incrementally to match other fields
            start_num = 1 if survey['skipcols'] > 0 else 0
            rename_dict = {name: f'date.{i + start_num}' for 
                           i, name in enumerate(sheet.columns[::4])}
            sheet = sheet.rename(rename_dict, axis=1).reset_index()
            sheet = sheet.rename({'x': 'x.0', 'y': 'y.0', 'z': 'z.0'}, axis=1)

            # Reshape data into long format
            profile_df = pd.wide_to_long(sheet, 
                                         stubnames=['date', 'x', 'y', 'z'], 
                                         i='index', 
                                         j='dropme', 
                                         sep='.').reset_index(drop=True)

            # Set datetimes
            profile_df['date'] = pd.to_datetime(profile_df.date, 
                                                errors='coerce',
                                                dayfirst=True)

            # Add profile metadata
            profile_df['beach'] = 'stirling'
            profile_df['section'] = 'all'
            profile_df['profile'] = profile_id
            profile_df['source'] = 'GPS survey'
            profile_df['start_x'] = start_x
            profile_df['start_y'] = start_y
            profile_df['id'] = (profile_df.beach + '_' + 
                                profile_df.section + '_' + 
                                profile_df.profile)

            # Add results to list
            output.append(profile_df.dropna())

    # Combine all survey and profile data
    profiles_df = pd.concat(output)

    # Reproject Perth Coastal Grid coordinates into Australian Albers
    pcg_crs = '+proj=tmerc +lat_0=0 +lon_0=115.8166666666667 ' \
              '+k=0.9999990600000001 +x_0=50000 +y_0=3800000 ' \
              '+ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'
    trans = Transformer.from_crs(pcg_crs, 'EPSG:3577', always_xy=True)
    profiles_df['x'], profiles_df['y'] =  trans.transform(
        profiles_df.y.values, profiles_df.x.values)
    profiles_df['start_x'], profiles_df['start_y'] =  trans.transform(
        profiles_df.start_y.values, profiles_df.start_x.values)

    # Calculate per-point distance from start of profile
    profiles_df['distance'] = profiles_df.apply(
        lambda x: Point(x.start_x, x.start_y).distance(Point(x.x, x.y)), axis=1)

    # Identify end of profiles by max distance from start, and merge back
    max_dist = (profiles_df.sort_values('distance', ascending=False)
                .groupby('id')['x', 'y']
                .first()
                .rename({'x': 'end_x', 'y': 'end_y'}, axis=1))
    profiles_df = profiles_df.merge(max_dist, on='id')

    # Find location and distance to water for datum height (e.g. 0 m AHD)
    intercept_df = profiles_df.groupby(['id', 'date']).apply(
        waterline_intercept, z_val=datum).dropna()   

     # Join into dataframe
    shoreline_dist = intercept_df.join(
        profiles_df.groupby(['id', 'date']).first())

    # Keep required columns
    shoreline_dist = shoreline_dist[['beach', 'section', 'profile',  
                                     'source', 'start_x', 'start_y', 
                                     'end_x', 'end_y', f'{datum}_dist', 
                                     f'{datum}_x', f'{datum}_y']]

    # Export to file
    shoreline_dist.to_csv(fname_out)
    

def preprocess_vicdeakin(fname,
                         datum=0):
    
    # Dictionary to map correct CRSs to locations
    crs_dict = {'apo': 'epsg:32754', 
                'cow': 'epsg:32755',
                'inv': 'epsg:32755',
                'leo': 'epsg:32755',
                'mar': 'epsg:32754',
                'pfa': 'epsg:32754',
                'por': 'epsg:32755',
                'prd': 'epsg:32755',
                'sea': 'epsg:32755',
                'wbl': 'epsg:32754'}

    # Read data
    profiles_df = pd.read_csv(fname,
                              parse_dates=['survey_date']).dropna()

    # Restrict to pre-2019
    profiles_df = profiles_df.loc[profiles_df.survey_date.dt.year < 2019]
    profiles_df = profiles_df.reset_index(drop=True)

    # Remove invalid profiles
    invalid = ((profiles_df.location == 'leo') & (profiles_df.tr_id == 94))
    profiles_df = profiles_df.loc[~invalid].reset_index(drop=True)

    # Extract coordinates
    coords = profiles_df.coordinates.str.findall(r'\d+\.\d+')
    profiles_df[['x', 'y']] = pd.DataFrame(coords.values.tolist(), 
                                           dtype=np.float32)

    # Add CRS and convert to Albers
    profiles_df['crs'] = profiles_df.location.apply(lambda x: crs_dict[x])
    profiles_df = profiles_df.groupby('crs', as_index=False).apply(
        lambda x: reproj_crs(x, in_crs=x.crs.iloc[0])).drop('crs', axis=1)
    profiles_df = profiles_df.reset_index(drop=True)

    # Convert columns to strings and add unique ID column
    profiles_df = profiles_df.rename({'location': 'beach', 
                                      'tr_id': 'profile', 
                                      'survey_date': 'date',
                                      'z': 'z_dirty',
                                      'z_clean': 'z'}, axis=1)
    profiles_df['profile'] = profiles_df['profile'].astype(str)
    profiles_df['section'] = 'all'
    profiles_df['source'] = 'drone'
    profiles_df['id'] = (profiles_df.beach + '_' + 
                         profiles_df.section + '_' + 
                         profiles_df.profile)
    
    # Reverse profile distances by subtracting max distance from each
    prof_max = profiles_df.groupby('id')['distance'].transform('max')
    profiles_df['distance'] = (profiles_df['distance'] - prof_max).abs()

    # Compute origin and end points for each profile and merge into data
    start_end_xy = profiles_from_dist(profiles_df)
    profiles_df = pd.merge(left=profiles_df, right=start_end_xy)
    
    # Export each beach
    for beach_name, beach in profiles_df.groupby('beach'):

        # Create output file name
        fname_out = f'output_data/vicdeakin_{beach_name}.csv'
        print(f'Processing {fname_out:<80}', end='\r')

        # Find location and distance to water for datum height (0 m AHD)
        intercept_df = beach.groupby(['id', 'date']).apply(
            waterline_intercept, z_val=datum).dropna()

        # If the output contains data
        if len(intercept_df.index) > 0:

            # Join into dataframe
            shoreline_dist = intercept_df.join(
                beach.groupby(['id', 'date']).first())

            # Keep required columns
            shoreline_dist = shoreline_dist[['beach', 'section', 'profile',  
                                             'source', 'start_x', 'start_y', 
                                             'end_x', 'end_y', f'{datum}_dist', 
                                             f'{datum}_x', f'{datum}_y']]

        # Export to file
        shoreline_dist.to_csv(fname_out)
        

def preprocess_nswbpd(fname, datum=0, overwrite=False):   
    
    # Get output filename
    name = Path(fname).stem.split('_')[-1].lower().replace(' ', '')
    fname_out = f'output_data/nswbpd_{name}.csv'
    
    # Test if file exists
    if not os.path.exists(fname_out) or overwrite:  
        
        # Read in data
        print(f'Processing {fname_out:<80}', end='\r')            
        profiles_df = pd.read_csv(fname, skiprows=5)
        profiles_df['Year/Date'] = pd.to_datetime(profiles_df['Year/Date'],
                                                  dayfirst=True,
                                                  errors='coerce')

        # Convert columns to strings and add unique ID column
        profiles_df['Beach'] = profiles_df['Beach'].str.lower().str.replace(' ', '')
        profiles_df['Block'] = profiles_df['Block'].astype(str).str.lower()
        profiles_df['Profile'] = profiles_df['Profile'].astype(str).str.lower()
        profiles_df['id'] = (profiles_df.Beach + '_' + 
                             profiles_df.Block + '_' + 
                             profiles_df.Profile)

        # Rename columns
        profiles_df.columns = ['beach', 'section', 'profile', 
                               'date', 'distance', 'z', 'x', 'y', 
                               'source', 'id']
        
        # Reproject coords to Albers
        trans = Transformer.from_crs('EPSG:32756', 'EPSG:3577', always_xy=True)
        profiles_df['x'], profiles_df['y'] = trans.transform(
            profiles_df.x.values, profiles_df.y.values)
        
        # Restrict to post 1987
        profiles_df = profiles_df[profiles_df['date'] > '1987']
        
        # Compute origin and end points for each profile and merge into data
        start_end_xy = profiles_from_dist(profiles_df)
        profiles_df = pd.merge(left=profiles_df, right=start_end_xy) 
        
        # Drop profiles that have been assigned incorrect profile IDs. 
        # To do this, we use a correlation test to determine whether x 
        # and y coordinates within each individual profiles fall along a 
        # straight line. If a profile has a low correlation (e.g. less 
        # than 99.9), it is likely that multiple profile lines have been 
        # incorrectly labelled with a single profile ID.
        valid_profiles = lambda x: x[['x', 'y']].corr().abs().iloc[0, 1] > 0.99
        drop = (~profiles_df.groupby('id').apply(valid_profiles)).sum()
        profiles_df = profiles_df.groupby('id').filter(valid_profiles)        
        if drop.sum() > 0: print(f'\nDropping invalid profiles: {drop:<80}')            
    
        # If profile data remains
        if len(profiles_df.index) > 0:
            
            # Restrict profiles to data that falls ocean-ward of the top of 
            # the foredune (the highest point in the profile) to remove 
            # spurious validation points, e.g. due to a non-shoreline lagoon 
            # at the back of the profile   
            foredune_dist = profiles_df.groupby(['id', 'date']).apply(
                lambda x: x.distance.loc[x.z.idxmax()]).reset_index(name='foredune_dist')
            profiles_df = pd.merge(left=profiles_df, right=foredune_dist) 
            profiles_df = profiles_df.loc[(profiles_df.distance >= 
                                           profiles_df.foredune_dist)]

            # Find location and distance to water for datum height (e.g. 0 m AHD)
            intercept_df = profiles_df.groupby(['id', 'date']).apply(
                waterline_intercept, z_val=datum).dropna()            
        
            # If any datum intercepts are found
            if len(intercept_df.index) > 0:

                # Join into dataframe
                shoreline_dist = intercept_df.join(
                    profiles_df.groupby(['id', 'date']).first())

                # Keep required columns
                shoreline_dist = shoreline_dist[['beach', 'section', 'profile',  
                                                 'source', 'foredune_dist', 
                                                 'start_x', 'start_y', 
                                                 'end_x', 'end_y', f'{datum}_dist', 
                                                 f'{datum}_x', f'{datum}_y']]

                # Export to file
                shoreline_dist.to_csv(fname_out)
    
    else:
        print(f'Skipping {fname:<80}', end='\r')


def preprocess_narrabeen(fname, 
                         fname_out='output_data/wrl_narrabeen.csv', 
                         datum=0,
                         overwrite=False):

    # Test if file exists
    if not os.path.exists(fname_out) or overwrite:

        #################
        # Location data #
        #################

        # Import data and parse DMS to DD
        print(f'Processing {fname_out:<80}', end='\r')
        data = "PF1 -33°42'20.65 151°18'16.30 118.42\n" \
               "PF2 -33°42'33.45 151°18'10.33 113.36\n" \
               "PF4 -33°43'01.55 151°17'58.84 100.26\n" \
               "PF6 -33°43'29.81 151°17'58.65 83.65\n" \
               "PF8 -33°43'55.94 151°18'06.47 60.48"
        coords = pd.read_csv(StringIO(data),
                             sep=' ',
                             names=['profile', 'y', 'x', 'angle'])
        coords['x'] = [dms2dd(i) for i in coords.x]
        coords['y'] = [dms2dd(i) for i in coords.y]

        # Extend survey lines out from start coordinates using supplied angle
        coords_end = coords.apply(
            lambda x: dist_angle(x.x, x.y, 0.002, x.angle), axis=1)
        coords = pd.concat([coords, coords_end], axis=1).drop('angle', axis=1)

        # Rename initial x and y values to indicate profile starting coords
        coords = coords.rename({'y': 'start_y', 'x': 'start_x'}, axis=1)

        # Reproject coords to Albers and create geodataframe
        trans = Transformer.from_crs('EPSG:4326', 'EPSG:3577', always_xy=True)
        coords['start_x'], coords['start_y'] = trans.transform(
            coords.start_x.values, coords.start_y.values)
        coords['end_x'], coords['end_y'] = trans.transform(
            coords.end_x.values, coords.end_y.values)

        # Add ID column
        coords['profile'] = coords['profile'].astype(str).str.lower()
        coords['beach'] = 'narrabeen'
        coords['section'] = 'all'
        coords['id'] = (coords.beach + '_' + 
                        coords.section + '_' + 
                        coords.profile)

        ###############
        # Survey data #
        ###############

        # Import data
        profiles_df = pd.read_csv(
            fname,
            usecols=[1, 2, 3, 4, 5],
            skiprows=1,
            parse_dates=['date'],
            names=['profile', 'date', 'distance', 'z', 'source'])

        # Restrict to post 1987
        profiles_df = profiles_df[(profiles_df.date.dt.year > 1987)]

        # Merge profile coordinate data into transect data
        profiles_df['profile'] = profiles_df['profile'].astype(str).str.lower()
        profiles_df = profiles_df.merge(coords, on='profile')

        # Add coordinates at every supplied distance along transects
        profiles_df[['x', 'y']] = profiles_df.apply(
            lambda x: pd.Series(dist_along_transect(x.distance, 
                                                    x.start_x, 
                                                    x.start_y, 
                                                    x.end_x, 
                                                    x.end_y)), axis=1)

        # Find location and distance to water for datum height (e.g. 0 m AHD)
        intercept_df = profiles_df.groupby(['id', 'date']).apply(
            waterline_intercept, z_val=datum).dropna()

        # If the output contains data
        if len(intercept_df.index) > 0:

            # Join into dataframe
            shoreline_dist = intercept_df.join(
                profiles_df.groupby(['id', 'date']).first())

            # Keep required columns
            shoreline_dist = shoreline_dist[['beach', 'section', 'profile', 
                                             'source', 'start_x', 'start_y',
                                             'end_x', 'end_y', f'{datum}_dist', 
                                             f'{datum}_x', f'{datum}_y']]

            # Export to file
            shoreline_dist.to_csv(fname_out)
            
    else:
        print(f'Skipping {fname:<80}', end='\r')
        
        
def preprocess_cgc(site, datum=0, overwrite=True):
    
    # Standardise beach name from site name
    beach = site.replace('NO*TH KIRRA', 'NORTH KIRRA').lower()
    beach = beach.replace(' ', '').lower()
    fname_out = f'output_data/cgc_{beach}.csv'
    print(f'Processing {fname_out:<80}', end='\r')
          
    # Test if file exists
    if not os.path.exists(fname_out) or overwrite:  
    
        # List of profile datasets to iterate through
        profile_list = glob.glob(f'input_data/cityofgoldcoast/{site}*.txt')

        # Output list to hold data
        site_profiles = []

        # For each profile, import and standardise data then add to list
        for profile_i in profile_list:

            # Identify unique field values from file string
            profile_string = os.path.basename(profile_i)
            date = profile_string.split(' - (')[1][-14:-4]
            section_profile = profile_string.split(' - (')[0].split(' - ')[1]
            section = section_profile.split(' ')[0]
            profile = ''.join(section_profile.split(' ')[1:])

            # Fix missing section or profile info
            if section and not profile:
                section, profile = 'na', section
            elif not section and not profile:
                section, profile = 'na', 'na'

            # Set location metadata and ID 
            profile_df = pd.read_csv(profile_i,
                                     usecols=[1, 2, 3],
                                     delim_whitespace=True, 
                                     names=['x', 'y', 'z'])
            profile_df['date'] = pd.to_datetime(date) 
            profile_df['source'] = 'hydrographic survey'
            profile_df['profile'] = profile.lower()
            profile_df['section'] = section.lower()
            profile_df['beach'] = beach
            profile_df['id'] = (profile_df.beach + '_' + 
                                profile_df.section + '_' + 
                                profile_df.profile)

            # Filter to drop pre-1987 and deep water samples, add to 
            # list if profile crosses 0
            profile_df = profile_df[profile_df.date > '1987']
            profile_df = profile_df[profile_df.z > -3.0]
            if (profile_df.z.min() < 0) & (profile_df.z.max() > 0):
                site_profiles.append(profile_df)

        # If list of profiles contain valid data
        if len(site_profiles) > 0:

            # Combine individual profiles into a single dataframe
            profiles_df = pd.concat(site_profiles)
            
            # Reproject coords to Albers
            trans = Transformer.from_crs('EPSG:32756', 'EPSG:3577', always_xy=True)
            profiles_df['x'], profiles_df['y'] = trans.transform(
                profiles_df.x.values, profiles_df.y.values)

            # Compute origin and end points for each profile
            start_xy = profiles_df.groupby(['id'], as_index=False).first()[['id', 'x', 'y']]
            end_xy = profiles_df.groupby(['id'], as_index=False).last()[['id', 'x', 'y']]
            start_xy = start_xy.rename({'x': 'start_x', 'y': 'start_y'}, axis=1)
            end_xy = end_xy.rename({'x': 'end_x', 'y': 'end_y'}, axis=1)

            # Join origin and end points into dataframe
            profiles_df = pd.merge(left=profiles_df, right=start_xy)
            profiles_df = pd.merge(left=profiles_df, right=end_xy)

            # Compute chainage
            profiles_df['distance'] = profiles_df.apply(
                lambda x: math.hypot(x.x - x.start_x, x.y - x.start_y), axis = 1)
            
            # Drop profiles that have been assigned incorrect profile IDs. 
            # To do this, we use a correlation test to determine whether x 
            # and y coordinates within each individual profiles fall along a 
            # straight line. If a profile has a low correlation (e.g. less 
            # than 99.9), it is likely that multiple profile lines have been 
            # incorrectly labelled with a single profile ID.
            valid_profiles = lambda x: x[['x', 'y']].corr().abs().iloc[0, 1] > 0.99
            drop = (~profiles_df.groupby('id').apply(valid_profiles)).sum()
            profiles_df = profiles_df.groupby('id').filter(valid_profiles)        
            if drop.sum() > 0: print(f'\nDropping invalid profiles: {drop:<80}')  

            # Restrict profiles to data that falls ocean-ward of the top of 
            # the foredune (the highest point in the profile) to remove 
            # spurious validation points, e.g. due to a non-shoreline lagoon 
            # at the back of the profile   
            foredune_dist = profiles_df.groupby(['id', 'date']).apply(
                lambda x: x.distance.loc[x.z.idxmax()]).reset_index(name='foredune_dist')
            profiles_df = pd.merge(left=profiles_df, right=foredune_dist) 
            profiles_df = profiles_df.loc[(profiles_df.distance >= 
                                           profiles_df.foredune_dist)]

            # Find location and distance to water for datum height (e.g. 0 m AHD)
            intercept_df = profiles_df.groupby(['id', 'date']).apply(
                waterline_intercept, z_val=datum).dropna()

            # If the output contains data
            if len(intercept_df.index) > 0:

                # Join into dataframe
                shoreline_dist = intercept_df.join(
                    profiles_df.groupby(['id', 'date']).first())

                # Keep required columns
                shoreline_dist = shoreline_dist[['beach', 'section', 'profile',  
                                                 'source', 'foredune_dist', 
                                                 'start_x', 'start_y', 
                                                 'end_x', 'end_y', f'{datum}_dist', 
                                                 f'{datum}_x', f'{datum}_y']]

                # Export to file
                shoreline_dist.to_csv(fname_out)
                
    else:
        print(f'Skipping {fname_out:<80}', end='\r')
        
        
def preprocess_tasmarc(site, datum=0, overwrite=True):
    
    def _tasmarc_metadata(profile):
    
        # Open file 
        with open(profile, 'r') as profile_data:

            # Load header data (first 20 rows starting with "#")
            header = takewhile(lambda x: x.startswith(('#', '&', ' ')), profile_data)
            header = list(header)[0:19]

            # List of metadata to extract
            meta_list = ['LONGITUDE', 'LATITUDE',  
                         'START DATE/TIME', 'TRUE BEARING TRANSECT DEGREES', 
                         'SURVEY METHOD']

            # Extract metadata for each metadata type in list
            meta_extract = map(
                lambda m: [row.replace(f'# {m} ', '').strip(' \n') 
                           for row in header if m in row][0], meta_list)
            lon, lat, date, bearing, source = meta_extract

            # Return metadata
            return {'lon': lon, 
                    'lat': lat, 
                    'date': date[0:10], 
                    'bearing': bearing, 
                    'source': source}

    # List of invalid profiles
    invalid_list = ['shelly_beach_north']  # incorrect starting coord
        
    # Set output name
    fname_out = f'output_data/tasmarc_{site}.csv'
    print(f'Processing {fname_out:<80}', end='\r')

    # Test if file exists
    if not os.path.exists(fname_out) or overwrite:         

        # List of profile datasets to iterate through
        profile_list = glob.glob(f'input_data/tasmarc/{site}/*.txt')
        
        # Remove invalid profiles
        profile_list = [profile for profile in profile_list if not 
                        any(invalid in profile for invalid in invalid_list)]

        # Output list to hold data
        site_profiles = []

        for profile in profile_list:

            # Load data and remove invalid data
            profile_df = pd.read_csv(profile, 
                                     comment='#', 
                                     delim_whitespace=True, 
                                     header=None,
                                     usecols=[0, 1, 2], 
                                     engine='python',
                                     names = ['distance', 'z', 'flag'])

            # Remove invalid data
            profile_df = profile_df[profile_df.flag == 2]
            profile_df = profile_df.drop('flag', axis=1)

            # Add metadata from file and coerce to floats
            profile_df = profile_df.assign(**_tasmarc_metadata(profile))
            profile_df = profile_df.apply(pd.to_numeric, errors='ignore')

            # Set to datetime
            profile_df['date'] = pd.to_datetime(profile_df['date'])
            profile_df = profile_df[profile_df.date > '1987']

            # Set remaining location metadata and ID
            profile_i = os.path.basename(profile).replace(site, '')[1:-15]
            profile_df['profile'] = (profile_i.replace('_', '') if 
                                     len(profile_i) > 0 else 'middle')
            profile_df['beach'] = site.replace('_', '') 
            profile_df['section'] = 'all'
            profile_df['id'] = (profile_df.beach + '_' + 
                                profile_df.section + '_' + 
                                profile_df.profile)

            # Filter to drop pre-1987 and deep water samples, add to list if any 
            # data is available above 0 MSL
            if (profile_df.z.min() < 0) & (profile_df.z.max() > 0):
                site_profiles.append(profile_df)

        # If list of profiles contain valid data
        if len(site_profiles) > 0:

            # Combine into a single dataframe
            profiles_df = pd.concat(site_profiles)

            # Extend survey lines out from start coordinates using supplied angle
            coords_end = profiles_df.apply(
                lambda x: dist_angle(x.lon, x.lat, 0.002, x.bearing), axis=1)
            profiles_df = pd.concat([profiles_df, coords_end], axis=1).drop('bearing', axis=1)

            # Rename fields
            profiles_df = profiles_df.rename({'lat': 'start_y', 'lon': 'start_x'}, axis=1)

            # Reproject coords to Albers and create geodataframe
            trans = Transformer.from_crs('EPSG:4326', 'EPSG:3577', always_xy=True)
            profiles_df['start_x'], profiles_df['start_y'] = trans.transform(
                profiles_df.start_x.values, profiles_df.start_y.values)
            profiles_df['end_x'], profiles_df['end_y'] = trans.transform(
                profiles_df.end_x.values, profiles_df.end_y.values)

            # Add coordinates for every distance along transects
            profiles_df[['x', 'y']] = profiles_df.apply(
                lambda x: pd.Series(dist_along_transect(x.distance,
                                                        x.start_x, 
                                                        x.start_y,
                                                        x.end_x, 
                                                        x.end_y)), axis=1)

            # Find location and distance to water for datum height (0 m AHD)
            intercept_df = (profiles_df.groupby(['id', 'date']).apply(
                waterline_intercept, z_val=datum).dropna())

            # If the output contains data
            if len(intercept_df.index) > 0:

                # Join into dataframe
                shoreline_dist = intercept_df.join(
                    profiles_df.groupby(['id', 'date']).first())

                # Keep required columns
                shoreline_dist = shoreline_dist[['beach', 'section', 'profile', 
                                                 'source', 'start_x', 'start_y',
                                                 'end_x', 'end_y', f'{datum}_dist', 
                                                 f'{datum}_x', f'{datum}_y']]

                # Export to file
                shoreline_dist.to_csv(fname_out)

        else:
            print(f'Skipping {fname_out:<80}', end='\r')
    

def waterbody_mask(input_data,
                   modification_data,
                   bbox):
    """
    Generates a raster mask for DEACoastLines based on the 
    SurfaceHydrologyPolygonsRegional.gdb dataset, and a vector 
    file containing minor modifications to this dataset (e.g. 
    features to remove or add to the dataset).
    
    The mask returns True for perennial 'Lake' features, any 
    'Aquaculture Area', 'Estuary', 'Watercourse Area', 'Salt 
    Evaporator', and 'Settling Pond' features. Features of 
    type 'add' from the modification data file are added to the
    mask, while features of type 'remove' are removed.
    """

    # Import SurfaceHydrologyPolygonsRegional data
    waterbody_gdf = gpd.read_file(input_data, bbox=bbox).to_crs(bbox.crs)

    # Restrict to coastal features
    lakes_bool = ((waterbody_gdf.FEATURETYPE == 'Lake') &
                  (waterbody_gdf.PERENNIALITY == 'Perennial'))
    other_bool = waterbody_gdf.FEATURETYPE.isin(['Aquaculture Area', 
                                                 'Estuary', 
                                                 'Watercourse Area', 
                                                 'Salt Evaporator', 
                                                 'Settling Pond'])
    waterbody_gdf = waterbody_gdf[lakes_bool | other_bool]

    # Load in modification dataset and select features to remove/add
    mod_gdf = gpd.read_file(modification_data, bbox=bbox).to_crs(bbox.crs)
    to_remove = mod_gdf[mod_gdf['type'] == 'remove']
    to_add = mod_gdf[mod_gdf['type'] == 'add']

    # Remove and add features
    if len(to_remove.index) > 0:
        if len(waterbody_gdf.index) > 0:
            waterbody_gdf = gpd.overlay(waterbody_gdf, to_remove, how='difference')        
    if len(to_add.index) > 0:
        if len(waterbody_gdf.index) > 0:
            waterbody_gdf = gpd.overlay(waterbody_gdf, to_add, how='union')
        else:
            waterbody_gdf = to_add
        
    return waterbody_gdf
        

def deacl_validation(val_path,
                     deacl_path,
                     datum=0,
                     sat_label='deacl',
                     val_label='val'):
    
    # Load validation data
    val_df = pd.read_csv(val_path, parse_dates=['date'])
    
    # Get title for plot
    title = val_df.beach.iloc[0].capitalize()

    # Get bounding box to load data for
    minx, maxy = val_df.min().loc[[f'{datum}_x', f'{datum}_y']]
    maxx, miny = val_df.max().loc[[f'{datum}_x', f'{datum}_y']]
    bbox = gpd.GeoSeries(box(minx, miny, maxx, maxy), crs='EPSG:3577')
    
    # Generate waterbody mask
    waterbody_gdf = waterbody_mask(
        input_data='../input_data/SurfaceHydrologyPolygonsRegional.gdb',
        modification_data='../input_data/estuary_mask_modifications.geojson',
        bbox=bbox)

    # Buffer by 100m and test what points fall within buffer
    # TODO: simplify using pandas geographic indexing e.g. .ix
    buffered_mask = waterbody_gdf.buffer(100).unary_union
    in_buffer = val_df.apply(
        lambda x: buffered_mask.contains(Point(x[f'{datum}_x'], 
                                               x[f'{datum}_y'])), axis=1)

    # Remove points that fall within buffer
    val_df = val_df.loc[~in_buffer]
    
    # Import corresponding waterline contours
    deacl_gdf = gpd.read_file(deacl_path, 
                              bbox=bbox.buffer(100)).to_crs('EPSG:3577')
    
    if (len(deacl_gdf.index) > 0) & (len(val_df.index) > 0):
    
        # Set year dtype to allow merging
        deacl_gdf['year'] = deacl_gdf.year.astype('int64')

        # Add year column
        val_df['year'] = val_df.date.dt.year

        # Aggregate by year and take most common categorical
        modal_vals = val_df[['source', 'beach', 'section', 'profile']].agg(
            lambda x: pd.Series.mode(x).iloc[0])
        
        # Aggregate by year and save count number and source
        counts = val_df.groupby(['year', 'id']).date.count()
        val_df = val_df.groupby(['year', 'id']).median()
        val_df['n'] = counts
        val_df = val_df.assign(**modal_vals.to_dict())
        val_df = val_df.reset_index()

        # Convert validation start and end locations to linestrings
        val_geometry = val_df.apply(
            lambda x: LineString([(x.start_x, x.start_y), 
                                  (x.end_x, x.end_y)]), axis=1)

        # Convert geometries to GeoDataFrame
        val_gdf = gpd.GeoDataFrame(data=val_df,
                                   geometry=val_geometry,
                                   crs='EPSG:3577').reset_index()

        # Match each shoreline contour to each date in validation data
        results_df = val_gdf.merge(deacl_gdf,
                                   on='year',
                                   suffixes=('_val', '_deacl'))

        # For each row, identify where profile intersects with waterline 
        results_df['intersect'] = results_df.apply(
            lambda x: x.geometry_val.intersection(x.geometry_deacl), 
            axis=1)
        
        # Drop any multipart geometries as these are invalid comparisons
        results_df = results_df[results_df.apply(
            lambda x: x.intersect.type == 'Point', axis=1)]
        results_df[f'{sat_label}_x'] = gpd.GeoSeries(results_df['intersect']).x
        results_df[f'{sat_label}_y'] = gpd.GeoSeries(results_df['intersect']).y
        
        # For each row, compute distance between origin and intersect
        results_df[f'{sat_label}_dist'] = results_df.apply(
            lambda x: x.intersect.distance(Point(x.start_x, x.start_y)), 
            axis=1)               
        
        # If data contains a foredune distance field, drop invalid 
        # validation points where DEA CoastLines intersection occurs 
        # behind the foredune 
        if 'foredune_dist' in results_df:
            valid = (results_df[f'{sat_label}_dist'] >= 
                     results_df.foredune_dist)
            results_df = results_df.loc[valid]
        
        # If enough data is returned:
        if len(results_df.index) > 0:
            
            # Rename for consistency    
            results_df = results_df.rename(
                    {f'{datum}_dist': f'{val_label}_dist',
                     f'{datum}_x': f'{val_label}_x',
                     f'{datum}_y': f'{val_label}_y'}, axis=1)
            
            # Calculate difference
            results_df['diff_dist'] = results_df.val_dist - results_df.deacl_dist
            
            return results_df[['id', 'year', 'beach', 'section', 
                               'profile', 'source', 'certainty', 'n', 
                               'start_x', 'start_y', 'end_x', 'end_y', 
                               f'{val_label}_x', f'{val_label}_y', f'{val_label}_dist', 
                               f'{sat_label}_x', f'{sat_label}_y', f'{sat_label}_dist',
                               'diff_dist']]

#             # Calculate stats
#             rmse = mean_squared_error(val_data, sat_data) ** 0.5
#             mae = mean_absolute_error(val_data, sat_data)
#             r2 = r2_score(val_data, sat_data)
#             cor = results_df[[sat_label, val_label]].corr().iloc[0, 1]
#             stats_dict = {'id': Path(val_path).stem, 
#                           'rmse': rmse, 'mae': mae, 'r2': r2, 'cor': cor}

#             # Plot image       
#             fig, ax = plt.subplots(figsize=(8.5, 7))
#             results_df.plot.scatter(x=val_label,
#                                     y=sat_label,
#                                     c=results_df.year,
#                                     s=25,
#                                     cmap='YlOrRd',
#                                     vmin=1987,
#                                     vmax=2018,
#                                     ax=ax, 
#                                     edgecolors='black',
#                                     linewidth=0.5
#                                    )
#             ax.plot(np.linspace(min(val_data.min(), sat_data.min()), 
#                                 max(val_data.max(), sat_data.max())),
#                     np.linspace(min(val_data.min(), sat_data.min()), 
#                                 max(val_data.max(), sat_data.max())),
#                     color='black',
#                     linestyle='dashed')
#             ax.set_title(title)
#             ax.annotate(f'RMSE: {rmse:.2f} m\n' \
#                         f'MAE: {mae:.2f} m\n' \
#                         f'R-squared: {r2:.2f}\n' \
#                         f'Correlation: {cor:.2f}', 
#                         xy=(0.05, 0.85),
#                         xycoords='axes fraction',
#                         fontsize=11)

#             # Export to file
#             fig.savefig(f'figures/{Path(val_path).stem}.png', 
#                         bbox_inches='tight', 
#                         dpi=50)

#             if eval_shapes:
#                 export_eval(results_df, 
#                             datum=datum,
#                             output_name=f'{Path(val_path).stem}')

#             if return_df:
#                 return [results_df, stats_dict]
#             else:
#                 return stats_dict
        
        
    
def main(argv=None):
    
    #########
    # Setup #
    #########
    
    if argv is None:

        argv = sys.argv
        print(sys.argv)

    # If no user arguments provided
    if len(argv) < 2:

        str_usage = "You must specify an analysis name"
        print(str_usage)
        sys.exit()
        
    # Set study area and name for analysis
    output_name = str(argv[1])
        

    ###############################
    # Load DEA CoastLines vectors #
    ###############################
    



if __name__ == "__main__":
    main()