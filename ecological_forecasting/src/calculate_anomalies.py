import numpy as np
import xarray as xr
import datacube 
import sys
sys.path.append('src')
import DEADataHandling
import query_from_shp

def calculate_anomalies(lat,lon,buffer,year,season,chunk_size):
    
    #Depending on the season, grab the time for the dc.load
    if season == 'DJF':
        time= (year + '-12', str(int(year)+1) + '-02')
    if season == 'MAM':
        time = (year + '-03', year + '-05')
    if season == 'JJA':
        time = (year + '-06', year + '-08')    
    if season == 'SON':
        time = (year + '-09', year + '-11')
    
    # generate query object
    query = {'lon': (lon - buffer, lon + buffer),
             'lat': (lat - buffer, lat + buffer),
             'time': time}

    # load data
    dc = datacube.Datacube(app='load_clearlandsat')
    ds = DEADataHandling.load_clearlandsat(dc=dc, query=query, sensors=['ls5','ls7','ls8'], 
                                           bands_of_interest=['nir', 'red'], lazy_load=True,
                                           dask_chunks = {'x': chunk_size, 'y': chunk_size}, 
                                           mask_pixel_quality=True,
                                           mask_invalid_data=True)
    
    # calculate the seasonal mean of MSAVI
    nir = ds.nir / 10000
    red = ds.red / 10000
    msavi = (2*nir+1-((2*nir+1)**2 - 8*(nir-red))**0.5)/2
    msavi = msavi.astype('float32') #convert to reduce memory
    msavi = msavi.mean('time').rename('msavi_mean')
    
    #get the bounding coords of the input ds to help index the climatology
    xmin, xmax = msavi.x.values[0], msavi.x.values[-1]
    ymin,ymax = msavi.y.values[0], msavi.y.values[-1]
    x_slice = [i+0.5 for i in range(int(xmin),int(xmax+25),25)]
    y_slice = [i-0.5 for i in range(int(ymin),int(ymax-25),-25)]
    
    #index the climatology dataset to the location of our AOI
    climatology = xr.open_rasterio('results/dcstats_test/msavi_climatology_'+ season +'_mosaic.tif',
                                  chunks=chunk_size).sel(x=x_slice, y=y_slice, method='nearest').squeeze()
    
    #test if the arrays match before we calculate the anomalies
    np.testing.assert_allclose(msavi.x.values, climatology.x.values)
    
    #calculate anomalies
    anomalies = msavi - climatology
    
    return anomalies

if __name__ == '__main__':
    calculate_anomalies(lat,lon,buffer,year,season,chunk_size)