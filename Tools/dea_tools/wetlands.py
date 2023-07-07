## wetlands.py
'''
This module is for processing DEA wetlands data. 

License: The code in this notebook is licensed under the Apache License, 
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth 
Australia data is licensed under the Creative Commons by Attribution 4.0 
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data 
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack 
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) 
using the `open-data-cube` tag (you can view previously asked questions 
here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, file one on 
Github: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new

Last modified: July 2023
'''

import pandas as pd

def normalise_wit(polygon_base_df):
    # ignore high pixel missing timestamp result
    polygon_base_df = polygon_base_df.dropna(subset=['bs'])
    
    # 1. compute the expected vegetation area total size: 1 - water (%) - wet (%)    
    polygon_base_df.loc[:, "veg_areas"] = 1 - polygon_base_df['water'] - polygon_base_df['wet']
    
    # 2. normalse the vegetation values based on vegetation size (to handle FC values more than 100 issue)
    # WARNNING: Not touch the water and wet, cause they are pixel classification result
    polygon_base_df.loc[:, "overall_veg_num"] = polygon_base_df['pv'] + polygon_base_df['npv'] + polygon_base_df['bs']
    
    # 3. if the overall_veg_num is 0, no need to normalize veg area
    norm_veg_index = polygon_base_df["overall_veg_num"] != 0
    
    for band in ["bs", "pv", "npv"]:
        polygon_base_df.loc[:, "norm_" + band] = polygon_base_df.loc[:, band]
        polygon_base_df.loc[norm_veg_index, "norm_" + band] = (
            polygon_base_df.loc[norm_veg_index, band]
            / polygon_base_df.loc[norm_veg_index, "overall_veg_num"]
            * polygon_base_df.loc[norm_veg_index, "veg_areas"]
        )
    
    # convert the string to Python datetime format, easy to do display the result in PNG
    polygon_base_df.loc[:, "date"] = pd.to_datetime(polygon_base_df["date"], infer_datetime_format=True)
    
    polygon_base_df.reset_index(inplace=True)
    
    return polygon_base_df