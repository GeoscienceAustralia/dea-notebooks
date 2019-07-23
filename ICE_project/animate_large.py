
import sys
import os
import pandas as pd
# from IPython.display import Image
import matplotlib.pyplot as plt
import fiona
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# import seaborn
from osgeo import gdal, ogr

# Import external dea-notebooks functions using relative link to Scripts directory
sys.path.append('src/')
import DEADataHandling
import DEAPlotting
from SpatialTools import geotransform
from SpatialTools import array_to_geotiff
from SpatialTools import rasterize_vector

directory = "/g/data/r78/cb3058/dea-notebooks/ICE_project/results/nmdb/"
suffix = "_Irrigated_OEHandLS_masked"

#list of years to help for-loop iterate through folders
x = range(1987,2019,1)
years = []
for i in x:
    nextyear = str(i + 1)[2:]
    y = str(i) + "_" + nextyear
    years.append(str(y))
# removing years that didn't work
years =  [e for e in years if e not in ('2011_12', '2012_13')]
years.sort()

#list of folders to help with loop
folders = os.listdir(directory)
folders.sort()

# Convert our shapefiles into tiffs, add them to an giant xarray and 
# then export as netcdf so we don't have to keep loading them while we
# work out the animation code.
def convertIrrShpToTiff(shp, year):  
    #open a tif and get transform info
    tif = shp[:77]+shp[77:95]+"_multithreshold_65Thres"+suffix[10:]+".tif"
    ds = xr.open_rasterio(tif).squeeze()
    transform, proj = geotransform(ds, (ds.x, ds.y), epsg=3577)
    rows,cols = ds.shape
    #turn vector in numpy array
    shp_arr = rasterize_vector(shp, cols=cols, rows=rows, geo_transform=transform, projection=proj)
    #convert numpy array inot xarray
    shp_xr = xr.DataArray(shp_arr, coords = [ds.y, ds.x], dims = ['y', 'x'])
    #append xarray to list
    da_list.append(shp_xr)

da_list = []
for year, folder in zip(years, folders): 
    print("\r", "working on year: " + year, end = '')
    convertIrrShpToTiff(directory+folder+"/"+"nmdb_Summer"+ year + suffix+".shp", year)

#generate date ranges to use as cooridnates in xrray dataset
dates = pd.date_range(start='1/1/1987', end='1/01/2019', freq='Y')
dates = dates.drop([pd.Timestamp('2011-12-31'), pd.Timestamp('2012-12-31')])
#concatenate all xarrays in list to a single multi-dim xarray with time ('dates') as coords.
da = xr.concat(da_list, dim=dates).rename({'concat_dim':'time'}).rename('Irrigated_Area')
#convert to dataset
ds = da.to_dataset()
#export netcdf
ds.to_netcdf("results/animations/NMDB_irrigation.nc")



# threeRivers = 'data/spatial/ThreeRivers.shp'
# ds = xr.open_dataset("results/animations/threeRivers_irrigation.nc")
# print("filling NaNs")
# ds = ds.fillna(0.1)

#get our irrigated area data, and scale it so numbers are similar to rainfall anomalies
# irr_area = pd.read_csv('results/nmdb_plots/csvs/NMDB_annual_area.csv')['irrigated area']
# mean_area = irr_area.mean()
# irr_anom = irr_area - mean_area
# scaledIrrAreaAnom = irr_anom / 1000

#load in rainfall anomaly data
# rain = pd.read_csv('data/mdb_rainfall.csv')
# rain = rain.drop([24,25])

# dates = pd.date_range(start='1/1/1987', end='1/01/2019', freq='Y')
# dates = dates.drop([pd.Timestamp('2011-12-31'), pd.Timestamp('2012-12-31')])

# df = pd.DataFrame({"Rainfall (mm)": list(rain.rain_anomaly_winter),
#                    "Irrigation (10^3 Ha)": list(scaledIrrAreaAnom)}, 
#                     index =dates)

# print("starting animation")
# DEAPlotting.animated_timeseriesline(ds, df, "results/animations/threeRivers_lineplot_fillNA_withShape.gif", 
#                                     width_pixels=1000, interval=300, bands=['Irrigated_Area'],onebandplot_cbar=False,
#                                     show_date=True, title= "Summer Irrigated Area", shapefile_path=threeRivers, 
#                                     shapefile_kwargs={'linewidth':1, 'edgecolor':'black',  'facecolor':"#00000000"},
#                                     onebandplot_kwargs={'cmap':'plasma'},
#                                     pandasplot_kwargs={'ylim': (-200,200), 'style':'o--'})

# shapefile_path=threeRivers,
#clipping to shapefile
# da = xr.open_dataset("results/animations/NMDB_irrigation.nc")
# transform, proj = geotransform(da.Irrigated_Area, (da.Irrigated_Area.x, da.Irrigated_Area.y), epsg=3577, alignment='centre')
# rows,cols = da.Irrigated_Area.shape[1:]
# shp_arr = rasterize_vector(threerivers, cols=cols, rows=rows, geo_transform=transform, projection=proj)

# da_clip = da.where(shp_arr)
# da_clip = da_clip.dropna(dim='x', how='all').dropna(dim='y', how='all')
# da_clip.to_netcdf("results/animations/threeRivers_irrigation.nc")