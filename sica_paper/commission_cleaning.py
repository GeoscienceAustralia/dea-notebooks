import sys
import os
import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr

results = "results/"

#FUNCTIONS for SCRIPT
def array_to_geotiff(fname, data, geo_transform, projection,
                     nodata_val=0, dtype=gdal.GDT_Float32):

    # Set up driver
    driver = gdal.GetDriverByName('GTiff')

    # Create raster of given size and projection
    rows, cols = data.shape
    dataset = driver.Create(fname, cols, rows, 1, dtype)
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)

    # Write data to array and set nodata values
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)
    band.SetNoDataValue(nodata_val)

    # Close file
    dataset = None

def geotransform(ds, coords, epsg=3577, alignment = 'centre', rotation=0.0):

    if alignment == 'centre':
        EW_pixelRes = float(coords[1][0] - coords[1][1])
        NS_pixelRes = float(coords[0][0] - coords[0][1])        
        east = float(coords[0][0]) - (EW_pixelRes/2)
        north = float(coords[1][0]) + (NS_pixelRes/2)
        
        transform = (east, EW_pixelRes, rotation, north, rotation, NS_pixelRes)
    
    elif alignment == 'upper_left':
        EW_pixelRes = float(coords[1][0] - coords[1][1])
        NS_pixelRes = float(coords[0][0] - coords[0][1])        
        east = float(coords[0][0])
        north = float(coords[1][0])
        
        transform = (east, EW_pixelRes, rotation, north, rotation, NS_pixelRes)
    
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    prj_wkt = srs.ExportToWkt()
    
    return transform, prj_wkt

def convertIrrShpToTiff(shp, year):  
    #open a tif and get transform info
    tif = shp[:77]+shp[77:95]+"_multithreshold_65Thres"+suffix[10:]+".tif"
    ds = xr.open_rasterio(tif).squeeze()
    transform, proj = geotransform(ds, (ds.x, ds.y), epsg=3577)
    rows,cols = ds.shape
    #turn vector into numpy array
    shp_arr = rasterize_vector(shp, cols=cols, rows=rows, geo_transform=transform, projection=proj)
    #convert numpy array into xarray
    shp_xr = xr.DataArray(shp_arr, coords = [ds.y, ds.x], dims = ['y', 'x'])
    #append xarray to list
    da_list.append(shp_xr)

#create parallized function for calculting sum and nanargmax
def count_irrigation(x, dim):
    return xr.apply_ufunc(np.sum, x, dask='parallelized',
                          input_core_dims=[[dim]],
                          kwargs={'axis': -1})

def IrrigationFirstOccurs(x, dim):
    """
    Calculating the time (indice) at which the first occurence of 
    Irrigation occurs (per-pixel). This works because np.nanargmax:
    "In cases of multiple occurrences of the maximum values,
    the indices corresponding to the first occurrence are returned."
    """
    return xr.apply_ufunc(np.nanargmax, x, dask='parallelized',
                          input_core_dims=[[dim]],
                          kwargs={'axis': -1})


#-----------SCRIPT-----------------
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

da_list = []
for year, folder in zip(years, folders): 
    print("\r", "working on year: " + year, end = '')
    convertIrrShpToTiff(directory+folder+"/"+"nmdb_Summer"+ year + suffix+".shp", year)

#generate date ranges to use as coordinates in xrray dataset
dates = pd.date_range(start='1/1/1987', end='1/01/2019', freq='Y')
dates = dates.drop([pd.Timestamp('2011-12-31'), pd.Timestamp('2012-12-31')])
#concatenate all xarrays into a single multi-dim xarray with time ('dates') as coords.
da = xr.concat(da_list, dim=dates).rename({'concat_dim':'time'}).rename('Irrigated_Area')
#convert to dataset
ds = da.to_dataset()
#export as netcdf
ds.to_netcdf(results + "NMDB_irrigation.nc")

#bring in data
irr_alltime = xr.open_dataset(results+'NMDB_irrigation.nc').astype(bool)

#generate various summary tiffs
count = count_irrigation(irr_alltime.Irrigated_Area, dim='time')
frequency = count / len(irr_alltime.time)
firstOccured = IrrigationFirstOccurs(irr_alltime.Irrigated_Area, dim='time')
yearsIrrigated = len(irr_alltime.time)-firstOccured 
normalisedFrequency = count / yearsIrrigated

#convert first observed to an array with the date (year)
dates = [t for t in range(1987,2019,1)]
dates =  [e for e in dates if e not in (2011, 2012)]
dates = np.asarray(dates)

def timey(ind, time):
    func = time[ind]
    return func

firstOccuredDates = timey(firstOccured, dates)

#mask out areas that return non-sensical values using the normalised frequency xarray
firstOccuredDates = np.where(normalisedFrequency.values > 0, firstOccuredDates, np.nan)
yearsIrrigated = yearsIrrigated.where(normalisedFrequency.values > 0)

#export geotiffs
transform, projection = geotransform(irr_alltime, (irr_alltime.x, irr_alltime.y), epsg=3577)

SpatialTools.array_to_geotiff(results+'rawFrequency_alltime.tif',
              frequency.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'count_alltime.tif',
              count.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'firstOccured_alltime.tif',
              firstOccured.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'firstOccuredDates_alltime.tif',
              firstOccuredDates, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'yearsIrrigated_alltime.tif',
              yearsIrrigated.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)

SpatialTools.array_to_geotiff(results+'normalisedFrequency_alltime.tif',
              normalisedFrequency.values, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)


#Now actually create the commission mask
freq = xr.open_rasterio(results+'normalisedFrequency_alltime.tif')
count = xr.open_rasterio(results+'count_alltime.tif')

freq_mask = np.where((freq.values <= 0.125) & (freq.values > 0), 1, 0)
count_mask = np.where((count.values == 1) & ((freq.values > 0.125) & (freq.values <= 0.25)), 1, 0)
combined_mask = np.where((freq_mask==1) | (count_mask==1), 1, 0)
transform, projection = geotransform(freq, (freq.x, freq.y), epsg=3577)

SpatialTools.array_to_geotiff(results+ "commission_mask.tif",
              combined_mask, geo_transform = transform, 
              projection = projection, 
              nodata_val=0)
