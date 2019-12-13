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
