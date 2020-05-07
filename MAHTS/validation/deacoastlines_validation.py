#!/usr/bin/env python
# coding: utf-8

# import sys
# import geopandas as gpd
# import pandas as pd
# from rtree import index
# from tqdm.auto import tqdm

# import deacoastlines_statistics as dcl_stats


    
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