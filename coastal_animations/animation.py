#!!!!!!!!!!!!
#User inputs
#!!!!!!!!!!!!

# shape_file = 'data/SA_aois2.shp'
masked_prop=0.10
# polygon_Num = 3

#--------------------------------
# Import modules
import datacube 
from datacube.utils import geometry
import sys
import os
import pandas as pd
from IPython.display import Image
import matplotlib.pyplot as plt
import fiona

# Import external dea-notebooks functions using relative link to Scripts directory
sys.path.append('src/')
import DEADataHandling
import DEAPlotting


# with fiona.open(shape_file) as shapes:
#     crs = geometry.CRS(shapes.crs_wkt) 
#     ShapesList = list(shapes)

# first_geometry = ShapesList[polygon_Num]['geometry']
# poly_name =ShapesList[polygon_Num]['properties']['name'].replace(' ','_')

# geom = geometry.Geometry(first_geometry, crs=crs)

# Set up datacube instance
dc = datacube.Datacube(app='Time series animation')

#Set up spatial and temporal query.
# query1987_97 = {'geopolygon': geom,
#          'time': ('1987-01-01', '1997-12-31')
#          }

# query1998_08 = {'geopolygon': geom,
#          'time': ('1998-01-01', '2008-12-31')
#          }

# query2009_19 = {'geopolygon': geom,
#          'time': ('2009-01-01', '2019-04-30')
#          }

queryAllTime = {'y':(-35.2, -35.4),
                'x': (148.85, 149.35),
                 'time': ('1987-01-01', '2019-04-30')
                 }

# querysentinel = {'geopolygon': geom,
#          'time': ('2015-01-01', '2019-05-30')
#          }
# querysentinel['resolution'] = (-10,10)
# querysentinel['output_crs'] = ('epsg:3577')


# Load in only clear Landsat observations with < 1% unclear values
print("retrieving data")

# ds_1987_97 = DEADataHandling.load_clearlandsat(dc=dc, query=query1987_97, 
#                                        bands_of_interest=['red', 'green', 'blue'], 
#                                        masked_prop=masked_prop) 

# ds_1998_08 = DEADataHandling.load_clearlandsat(dc=dc, query=query1998_08, 
#                                        bands_of_interest=['red', 'green', 'blue'], 
#                                        masked_prop=masked_prop) 

# ds_2009_19 = DEADataHandling.load_clearlandsat(dc=dc, query=query2009_19, 
#                                        bands_of_interest=['red', 'green', 'blue'], 
#                                        masked_prop=masked_prop) 

ds_allTime = DEADataHandling.load_clearlandsat(dc=dc, query=queryAllTime, 
                                       bands_of_interest=['red', 'green', 'blue'], 
                                       masked_prop=masked_prop) 

# print("creating animation 1")                                       
# DEAPlotting.animated_timeseries(ds=ds_1987_97, 
#             output_path="results/" + f'{poly_name}_1987_97_animated_timeseries.gif', 
#             interval=500) 
# print("creating animation 2")            
# DEAPlotting.animated_timeseries(ds=ds_1998_08,
#                                 output_path="results/" + f'{poly_name}_1998_08_animated_timeseries.gif', 
#                                 interval=500) 
# print("creating animation 3")                              
# DEAPlotting.animated_timeseries(ds=ds_2009_19,
#                                 output_path="results/"+ f'{poly_name}_2009_19_animated_timeseries.gif', 
#                                 interval=500) 
print("creating animation 4")                                
DEAPlotting.animated_timeseries(ds=ds_allTime,percentile_stretch = (0.05, 0.95),
                                output_path='results/canberra_allTime_cloudy_animated_timeseries2.gif', 
                                interval=50)     
print("finished")