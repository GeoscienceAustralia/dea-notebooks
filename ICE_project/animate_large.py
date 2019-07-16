
import sys
import os
import pandas as pd
from IPython.display import Image
import matplotlib.pyplot as plt
import fiona
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn
from osgeo import gdal, ogr

# Import external dea-notebooks functions using relative link to Scripts directory
sys.path.append('src/')
import DEADataHandling
import DEAPlotting
from SpatialTools import geotransform
from SpatialTools import array_to_geotiff
from SpatialTools import rasterize_vector

threeRivers = 'data/spatial/ThreeRivers.shp'
ds = xr.open_dataset("results/animations/threeRivers_irrigation.nc")
print("filling NaNs")
ds = ds.fillna(0.1)

#get our irrigated area data, and scale it so numbers are similar to rainfall anomalies
irr_area = pd.read_csv('results/nmdb_plots/csvs/NMDB_annual_area.csv')['irrigated area']
mean_area = irr_area.mean()
irr_anom = irr_area - mean_area
scaledIrrAreaAnom = irr_anom / 1000

#load in rainfall anomaly data
rain = pd.read_csv('data/mdb_rainfall.csv')
rain = rain.drop([24,25])

dates = pd.date_range(start='1/1/1987', end='1/01/2019', freq='Y')
dates = dates.drop([pd.Timestamp('2011-12-31'), pd.Timestamp('2012-12-31')])

df = pd.DataFrame({"Rainfall (mm)": list(rain.rain_anomaly_winter),
                   "Irrigation (10^3 Ha)": list(scaledIrrAreaAnom)}, 
                    index =dates)

print("starting animation")
DEAPlotting.animated_timeseriesline(ds, df, "results/animations/threeRivers_lineplot_fillNA_withShape.gif", 
                                    width_pixels=1000, interval=300, bands=['Irrigated_Area'],onebandplot_cbar=False,
                                    show_date=True, title= "Summer Irrigated Area", shapefile_path=threeRivers, 
                                    shapefile_kwargs={'linewidth':1, 'edgecolor':'black',  'facecolor':"#00000000"},
                                    onebandplot_kwargs={'cmap':'plasma'},
                                    pandasplot_kwargs={'ylim': (-200,200), 'style':'o--'})

# shapefile_path=threeRivers,
#clipping to shapefile
# da = xr.open_dataset("results/animations/NMDB_irrigation.nc")
# transform, proj = geotransform(da.Irrigated_Area, (da.Irrigated_Area.x, da.Irrigated_Area.y), epsg=3577, alignment='centre')
# rows,cols = da.Irrigated_Area.shape[1:]
# shp_arr = rasterize_vector(threerivers, cols=cols, rows=rows, geo_transform=transform, projection=proj)

# da_clip = da.where(shp_arr)
# da_clip = da_clip.dropna(dim='x', how='all').dropna(dim='y', how='all')
# da_clip.to_netcdf("results/animations/threeRivers_irrigation.nc")