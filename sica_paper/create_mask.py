### merging the dry years to create a mask
## Find dry and average rainfall years using standardised anomalies. 
# BARRA rainfall data. 1990 to 2019. Anomaly caluclated using 1990-12 to 2011-02 baseline. 
# The dry years are calculated using the rainfall script that identifies
# standardised rainfall anomalies. dry= DJF < 0.5 std.dev, SON < 0.5 Std.dev
# Merging with the OEH 2017 'irrigated' polygons to fther reduce omission errors

import geopandas as gpd
import pandas as pd
import xarray as xr

#USER INPUTS
directory = "/g/data/r78/cb3058/dea-notebooks/sica_paper/results/nmdb/"
suffix = "_80polys_10ha"
rainfall_data = '../data/NMDB_rainfall_STD_anomaly.nc'
std_dev_thres = 0.5

#FIND THE DRY YEARS
print('finding dry years')
rain = xr.open_dataarray(rainfall_data)
djf = rain[2:][::4]
son = rain[1:][::4]

zonal_djf = djf.mean(['x', 'y'])
zonal_son = son.mean(['x', 'y'])

dry_djf = zonal_djf[zonal_djf < std_dev_thres]
dry_djf = list(pd.DatetimeIndex(dry_djf.time.values).year)

dry_son = zonal_son[zonal_son<std_dev_thres]
dry_son = list(pd.DatetimeIndex(dry_son.time.values).year)

dry_years = list(set(dry_son).intersection(dry_djf))
dry_years.extend([1987,1988,1989]) #add years before BARRA data
dry_years.sort()

#convert dry years to strings for file operations
years = []
for i in dry_years:
    nextyear = str(i + 1)[2:]
    y = str(i) + "_" + nextyear
    years.append(str(y))
# removing years that didn't work
years =  [e for e in years if e not in ('2011_12', '2012_13')]
years.sort()

#add dry-year shapefiles to a list
print('merging dry-years shapefiles')
shapes = []
for year in years:
    x = gpd.read_file(directory+"nmdb_"+year+"/nmdb_Summer"+year+suffix+".shp")
    shapes.append(x)

#APPEND OEH2017 LAYER
oeh = gpd.read_file('../data/nmdb_OEH2017_irrigated.shp')
oeh = oeh.to_crs(shapes[0].crs)
shapes.append(oeh)

#create initial mask
mask_interim = pd.concat(shapes, sort=False)

print('fixing invalid polys')
mask_valid = mask_interim.where(mask_interim.is_valid)
mask_valid = mask_valid.dropna(axis=0,how = 'all')

mask_invalid = mask_interim[~mask_interim.is_valid]
mask_invalid.loc[:,'geometry'] = mask_invalid.geometry.buffer(0.0001)
mask_invalid = mask_invalid.set_geometry('geometry')
mask_invalid = mask_invalid.dropna(axis=0,how = 'all')

#recombine polys and dissolve into single polygon
mask = pd.concat([mask_valid,mask_invalid], sort=False)
mask['DISS_ID'] = 1
mask = mask.dissolve(by='DISS_ID', aggfunc='sum')

print('exporting mask')
mask.to_file('../data/nmdb_LSandOEH_mask_dirty.shp')

