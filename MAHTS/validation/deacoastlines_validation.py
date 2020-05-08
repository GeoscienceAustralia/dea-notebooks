#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from shapely.geometry import box
import geopandas as gpd


def interp_intercept(x, y1, y2, reverse=True):
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
            C = (p1[0]*p2[1] - p2[0]*p1[1])
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
        xc, yc = intercept((x[idx], y1[idx]),((x[idx+1], y1[idx+1])), 
                           ((x[idx], y2[idx])), ((x[idx+1], y2[idx+1])))

        return xc[0][0]
    
    except: 
        
        return np.nan
    

def preprocess_nswbpd(fname):
    
    # Read in data
    print(fname, end='\r')
    profiles_df = pd.read_csv(fname, skiprows=5)
    profiles_df['Year/Date'] = pd.to_datetime(profiles_df['Year/Date'],
                                              dayfirst=True,
                                              errors='coerce')

    # Restrict to post 1987
    profiles_df = profiles_df[profiles_df['Year/Date'] > '1987']

    # Convert columns to strings and add unique ID column
    profiles_df['Beach'] = profiles_df['Beach'].str.lower().str.replace(' ', '')
    profiles_df['Block'] = profiles_df['Block'].astype(str).str.lower()
    profiles_df['Profile'] = profiles_df['Profile'].astype(str).str.lower()
    profiles_df['site'] = profiles_df[['Beach', 'Block',
                                       'Profile']].apply('_'.join, 1)

    # Rename columns
    profiles_df.columns = ['beach', 'section', 'profile', 'date', 'chainage', 
                           'elevation', 'easting', 'northing', 'source', 'site']

    # Compute origin points for each profile
    start_xy = profiles_df.loc[profiles_df.groupby(['site']).chainage.idxmin(), 
                                ['site', 'easting', 'northing']]
    start_xy = start_xy.rename({'easting': 'start_x', 'northing': 'start_y'}, axis=1)
    start_xy = start_xy.reset_index(drop=True)

    # Compute end points for each profile
    end_xy = profiles_df.loc[profiles_df.groupby(['site']).chainage.idxmax(), 
                             ['site', 'easting', 'northing']]
    end_xy = end_xy.rename({'easting': 'end_x', 'northing': 'end_y'}, axis=1)
    end_xy = end_xy.reset_index(drop=True)

    # Join origin and end points into dataframe
    profiles_df = pd.merge(left=profiles_df, right=start_xy)
    profiles_df = pd.merge(left=profiles_df, right=end_xy)

    # Find location and distance to water for datum height (0 m AHD)
    out = (profiles_df
           .groupby(['site', 'date'])
           .apply(lambda x: pd.Series({
              '0_dist': interp_intercept(x.chainage.values, 
                                         x.elevation.values, 0),
              '0_x': interp_intercept(x.easting.values, 
                                      x.elevation.values, 0),
              '0_y': interp_intercept(x.northing.values, 
                                      x.elevation.values, 0)}))
           .dropna())

    # If the output contains data
    if len(out.index):

        # Join into dataframe
        shoreline_dist = out.join(profiles_df.groupby(['site', 'date']).first())

        # Keep required columns
        shoreline_dist = shoreline_dist[['beach', 'section', 'profile',  
                                         'source', 'start_x', 'start_y', 'end_x', 
                                         'end_y', '0_dist', '0_x', '0_y']]

        # Export to file
        shoreline_dist.to_csv(f'output_data/nswbpd_{shoreline_dist.beach.iloc[0]}.csv')
        
    
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