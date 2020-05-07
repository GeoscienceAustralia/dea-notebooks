#!/usr/bin/env python
# coding: utf-8

import sys
import geopandas as gpd
import pandas as pd
from rtree import index
from tqdm.auto import tqdm

import deacoastlines_statistics as dcl_stats


def points_in_poly(points, polygons):

    # Create the R-tree index and store the features in it (bounding box)   
    idx = index.Index()
    for pos, poly in enumerate(tqdm(polygons, desc='Building index')):
        idx.insert(pos, poly.bounds)

    # Iterate through points
    out_dict = {}
    for i, point in enumerate(tqdm(points, desc='Processing points')):
        poly_ids = [j for j in idx.intersection((point.coords[0]))
                    if point.within(polygons[j])]
        out_dict[i] = poly_ids

#     # Re-order output dictionary
#     poly_points_dict = {}
#     for point_id, poly_ids in out_dict.items():
#         for poly_id in poly_ids:
#             poly_points_dict.setdefault(poly_id, []).append(point_id)
    
    return out_dict


def get_matching_data(key, stats_gdf, poly_points_dict, min_n=100):

    matching_points = stats_gdf.iloc[poly_points_dict[key]].copy()

    if len(matching_points.index) > min_n:

        # Set nonsignificant to 0
        matching_points.loc[matching_points.sig_time > 0.01, 'rate_time'] = 0

        return pd.Series([matching_points.rate_time.mean(),
                          len(matching_points.index)])

    else:
        return pd.Series([None, None])

    
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
    
    stats_gdf = gpd.read_file(f'DEACoastLines_statistics_{output_name}.shp').to_crs('EPSG:3577')
    contours_gdf = gpd.read_file(f'DEACoastLines_coastlines_{output_name}.shp')
    # stats_gdf = gpd.read_file(f'output_data/1193_v0.2.0/vectors/shapefiles/stats_1193_v0.2.0_mndwi_0.00.shp').to_crs('EPSG:3577')
    # contours_gdf = gpd.read_file(f'output_data/1193_v0.2.0/vectors/shapefiles/contours_1193_v0.2.0_mndwi_0.00.shp')

    contours_gdf = (contours_gdf
                    .loc[contours_gdf.geometry.is_valid]
                    .to_crs('EPSG:3577')
                    .set_index('year'))

    summary_gdf = dcl_stats.stats_points(contours_gdf, 
                                         baseline_year='2018', 
                                         distance=3000)
    
    ####################
    # Generate summary #
    ####################

    # Generate dictionary of polygon IDs and corresponding points
    poly_points_dict = points_in_poly(points=summary_gdf.geometry, 
                                      polygons=stats_gdf.buffer(6000))

    # Compute mean and number of obs for each polygon
    summary_gdf[['rate_time', 'n']] = summary_gdf.apply(
        lambda row: get_matching_data(row.name, 
                                      stats_gdf,
                                      poly_points_dict,
                                      min_n=100), axis=1)

    # Export to file
    summary_gdf.to_file(f'DEACoastLines_summary_{output_name}.shp')


if __name__ == "__main__":
    main()