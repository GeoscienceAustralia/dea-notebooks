import numpy as np
import xarray as xr
import fiona
import math
import rasterio.features
import datacube 
import warnings
from datacube.storage import masking
from datacube.utils import geometry
from datacube.helpers import ga_pq_fuser
import folium
from pyproj import Proj, transform
import geopandas as gpd
import ipywidgets
import matplotlib as mpl
from ipyleaflet import Map, Marker, Popup, GeoJSON, basemaps

def load_landsat(dc, query, sensors=('ls5', 'ls7', 'ls8'), product='nbart', dask_chunks = {'time': 1},
                      lazy_load = False, bands_of_interest=None, ls7_slc_off=False,):


    #######################
    # Process each sensor #
    #######################    
    # Due to possible bug in xarray 0.13.0, define temporary function 
    # which converts dtypes in a way that preserves attributes
    def astype_attrs(da, dtype=np.float32):
        '''
        Loop through all data variables in the dataset, record 
        attributes, convert to float32, then reassign attributes. If 
        the data variable cannot be converted to float32 (e.g. for a
        non-numeric dtype like strings), skip and return the variable 
        unchanged.
        '''
        
        try:            
            da_attr = da.attrs
            da = da.astype(dtype)
            da = da.assign_attrs(**da_attr)
            return da
        
        except ValueError:        
            return da
    
    
    # Dictionary to save results from each sensor 
    filtered_sensors = {}

    # Iterate through all sensors, returning only observations with > mask_prop clear pixels
    for sensor in sensors:     
        
            # Load PQ data using dask
            print(f'Loading {sensor}')
            
            # If bands of interest are given, assign measurements in dc.load call. This is
            # for compatibility with the existing dea-notebooks load_nbarx function.
            if bands_of_interest:
                
                # Lazily load Landsat data using dask              
                data = dc.load(product=f'{sensor}_{product}_albers',
                               measurements=bands_of_interest,
                               group_by='solar_day', 
                               dask_chunks=dask_chunks,
                               **query)

            # If no bands of interest given, run without specifying measurements, and 
            # therefore return all available bands
            else:
                
                # Lazily load Landsat data using dask  
                data = dc.load(product=f'{sensor}_{product}_albers',
                               group_by='solar_day', 
                               dask_chunks=dask_chunks,
                               **query)             

            # Load PQ data
            pq = dc.load(product=f'{sensor}_pq_albers',
                         group_by='solar_day',
                         fuse_func=ga_pq_fuser,
                         dask_chunks=dask_chunks,
                         **query)            
            
            # If resulting dataset has data, continue:
            if data.variables:
                
                # Remove Landsat 7 SLC-off from PQ layer if ls7_slc_off=False
                if not ls7_slc_off and sensor == 'ls7':

#                     print('    Ignoring SLC-off observations for ls7')
                    data = data.sel(time=data.time < np.datetime64('2003-05-30')) 
                
                # If more than 0 timesteps
                if len(data.time) > 0:                       

                    # Return only Landsat observations that have matching PQ data 
                    time = (data.time - pq.time).time
                    data = data.sel(time=time)
                    pq = pq.sel(time=time)

                    # Identify pixels with no clouds in either ACCA for Fmask
                    good_quality = masking.make_mask(pq.pixelquality,                         
                                                     cloud_acca='no_cloud',
                                                     cloud_shadow_acca='no_cloud_shadow',
                                                     cloud_shadow_fmask='no_cloud_shadow',
                                                     cloud_fmask='no_cloud',
                                                     blue_saturated=False,
                                                     green_saturated=False,
                                                     red_saturated=False,
                                                     nir_saturated=False,
                                                     swir1_saturated=False,
                                                     swir2_saturated=False,
                                                     contiguous=True)
                   
  
                    ds = data.apply(astype_attrs, dtype=np.float32, keep_attrs=True)
                    filtered = ds.where(good_quality)

                    # Add result to dictionary
                    if lazy_load==True:
                        filtered_sensors[sensor] = filtered
                    else:
                        filtered_sensors[sensor] = filtered.compute()

                    # Close datasets
                    filtered = None
                    good_quality = None
                    data = None
                    pq = None            

                else:
                    
                    # If there is no data for sensor or if another error occurs:
                    print(f'    Skipping {sensor}; no valid data for query')
                    
            else:

                # If there is no data for sensor or if another error occurs:
                print(f'    Skipping {sensor}; no valid data for query')
                
                
    ############################
    # Combine multiple sensors #
    ############################
                
    # Proceed with concatenating only if there is more than 1 sensor processed
    if len(filtered_sensors) > 1:

        # Concatenate all sensors into one big xarray dataset, and then sort by time 
        sensor_string = ", ".join(filtered_sensors.keys())
        print(f'Combining and sorting {sensor_string} data')
        combined_ds = xr.concat(filtered_sensors.values(), dim='time')
        combined_ds = combined_ds.sortby('time')                                                               
      
        combined_ds = combined_ds.apply(astype_attrs, 
                                        dtype=np.float32, 
                                        keep_attrs=True)
        combined_ds = masking.mask_invalid_data(combined_ds)
        
        # reset pixel quality attributes
        if product == 'pq':
            combined_ds.pixelquality.attrs.update(list(filtered_sensors.values())[0].pixelquality.attrs)
        
        # Return combined dataset
        return combined_ds
    
    # Return the single dataset if only one sensor was processed
    elif len(filtered_sensors) == 1:
        
        sensor_string = ", ".join(filtered_sensors.keys())
        sensor_ds = list(filtered_sensors.values())[0]
        
        sensor_ds = masking.mask_invalid_data(sensor_ds)       
        
        return sensor_ds
    
    else:
        
        print(f'No data returned for query for any sensor in {", ".join(sensors)} '
              f'and time range {"-".join(query["time"])}')


def calculate_anomalies(veg_index, from_shape, shp_fpath,
                        year, season, region, lat, lon, buffer, chunk_size):
    
    #error messaging for important inputs
    if veg_index not in ('msavi', 'ndvi'):
        raise ValueError("Veg_index must be either 'msavi' or 'ndvi'")
    
    if season not in ('DJF','MAM','JJA','SON'):
        raise ValueError("Not a valid season, "
                         "must be one of 'DJF', 'MAM, 'JJA' or 'SON'")
    if from_shape:
        if len(fiona.open(shp_fpath)) > 1:
            warnings.warn("This script can only accept shapefiles with a single polygon feature; "
                          "seasonal anomalies will be calculated for the extent of the "
                          "first geometry in the shapefile only.")
        
    #Depending on the season, grab the time for the dc.load
    if season == 'DJF':
        time= (year + '-12', str(int(year)+1) + '-02')
    if season == 'MAM':
        time = (year + '-03', year + '-05')
    if season == 'JJA':
        time = (year + '-06', year + '-08')    
    if season == 'SON':
        time = (year + '-09', year + '-11')
    
    #connect to datacube
    dc = datacube.Datacube(app='load_clearlandsat')
    
    #get data from shapefile extent and mask
    if from_shape:
        print("extracting data based on shapefile extent")
        
        with fiona.open(shp_fpath) as input:
            crs = geometry.CRS(input.crs_wkt)
        
        feat = fiona.open(shp_fpath)[0]
        first_geom = feat['geometry']
        geom = geometry.Geometry(first_geom, crs=crs)

        query = {'geopolygon': geom,
                 'time': time}
        
        ds = load_landsat(dc=dc, query=query, sensors=['ls5','ls7','ls8'], 
                           bands_of_interest=['nir', 'red'], lazy_load=True,
                           dask_chunks = {'x': chunk_size, 'y': chunk_size})
        
        mask = rasterio.features.geometry_mask([geom.to_crs(ds.geobox.crs)for geoms in [geom]],
                                       out_shape=ds.geobox.shape,
                                       transform=ds.geobox.affine,
                                       all_touched=False,
                                       invert=False)
        
        mask_xr = xr.DataArray(mask, dims = ('y','x'))
        ds = ds.where(mask_xr==False)
        
    else: 
        print('Extracting data based on lat, lon coords')
        query = {'lon': (lon - buffer, lon + buffer),
                 'lat': (lat - buffer, lat + buffer),
                 'time': time}
        
        ds = load_landsat(dc=dc, query=query, sensors=['ls5','ls7','ls8'], 
                           bands_of_interest=['nir', 'red'], lazy_load=True,
                           dask_chunks = {'x': chunk_size, 'y': chunk_size})

    
    print('calculating vegetation indice')
    
    if veg_index == 'msavi':
        # calculate the seasonal mean of MSAVI
        nir = ds.nir / 10000
        red = ds.red / 10000
        vegIndex = (2*nir+1-((2*nir+1)**2 - 8*(nir-red))**0.5)/2
        vegIndex = vegIndex.astype('float32')
        vegIndex = vegIndex.mean('time').rename(veg_index+'_mean')
    
    if veg_index == 'ndvi':
        vegIndex = (ds.nir - ds.red) / (ds.nir + ds.red)
        vegIndex = vegIndex.astype('float32')
        vegIndex = vegIndex.mean('time').rename(veg_index+'_mean')
        
    #get the bounding coords of the input ds to help with indexing the climatology
    xmin, xmax = vegIndex.x.values[0], vegIndex.x.values[-1]
    ymin,ymax = vegIndex.y.values[0], vegIndex.y.values[-1]
    x_slice = [i+0.5 for i in range(int(xmin),int(xmax+25),25)]
    y_slice = [i-0.5 for i in range(int(ymin),int(ymax-25),-25)]
    
    #index the climatology dataset to the location of our AOI
    print('Opening climatology for: ' + veg_index + "_"+ region + '_climatology_'+ season)
    climatology = xr.open_rasterio('results/' + veg_index + "_"+region+ '_climatology_'+ season +'_mosaic.tif',
                                  chunks=chunk_size).sel(x=x_slice, y=y_slice, method='nearest').squeeze()
    
    #test if the arrays match before we calculate the anomalies
    np.testing.assert_allclose(vegIndex.x.values, climatology.x.values,
                              err_msg="The X coordinates on the AOI dataset do not match "
                                      "the X coordinates on the climatology dataset. "
                                       "You're AOI may be beyond the extent of the pre-computed "
                                       "climatology dataset.")
    
    np.testing.assert_allclose(vegIndex.y.values, climatology.y.values,
                          err_msg="The Y coordinates on the AOI dataset do not match "
                                  "the Y coordinates on the climatology dataset. "
                                   "You're AOI may be beyond the extent of the pre-computed "
                                   "climatology dataset.")
    
    print('calculating anomalies')
    #calculate anomalies
    anomalies = vegIndex - climatology
    
    #add back metadata
    anomalies = anomalies.rename(veg_index + '_anomalies').to_dataset()
    anomalies.attrs = ds.attrs
    anomalies.attrs['units'] = 1

    return anomalies


# Define function to assist `display_map` in selecting a zoom level for plotting
def _degree_to_zoom_level(l1, l2, margin = 0.0):
    
    """
    Helper function to set zoom level for `display_map`
    """
    
    degree = abs(l1 - l2) * (1 + margin)
    zoom_level_int = 0
    if degree != 0:
        zoom_level_float = math.log(360 / degree) / math.log(2)
        zoom_level_int = int(zoom_level_float)
    else:
        zoom_level_int = 18
    return zoom_level_int

def map_shapefile(gdf, 
                  weight=2, 
                  colormap=mpl.cm.YlOrRd, 
                  basemap=basemaps.Esri.WorldImagery, 
                  default_zoom=None,
                  hover_col=None,
                  hover_prefix=''):
    
    """
    Plots a geopandas GeoDataFrame over an interactive ipyleaflet 
    basemap. Optionally, can be set up to print selected data from 
    features in the GeoDataFrame. 
    
    Last modified: October 2019
    
    Parameters
    ----------  
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing the spatial features to be plotted 
        over the basemap
    weight : float or int, optional
        An optional numeric value giving the weight that line features
        will be plotted as. Defaults to 2; larger numbers = thicker
    colormap : matplotlib.cm, optional
        An optional matplotlib.cm colormap used to style the features
        in the GeoDataFrame. Features will be coloured by the order
        they appear in the GeoDataFrame. Defaults to the `YlOrRd` 
        colormap.
    basemap : ipyleaflet.basemaps object, optional
        An optional ipyleaflet.basemaps object used as the basemap for 
        the interactive plot. Defaults to `basemaps.Esri.WorldImagery`
    default_zoom : int, optional
        An optional integer giving a default zoom level for the 
        interactive ipyleaflet plot. Defaults to 13
    hover_col : str, optional
        An optional string giving the name of any column in the
        GeoDataFrame you wish to have data from printed above the 
        interactive map when a user hovers over the features in the map.
        Defaults to None which will not print any data. 
    """
    
    def n_colors(n, colormap=colormap):
        data = np.linspace(0.0,1.0,n)
        c = [mpl.colors.rgb2hex(d[0:3]) for d in colormap(data)]
        return c

    def data_to_colors(data, colormap=colormap):
        c = [mpl.colors.rgb2hex(d[0:3]) for 
             d in colormap(mpl.colors.Normalize()(data))]
        return c 
    
    def on_hover(event, id, properties):
        with dbg:
            text = properties.get(hover_col, '???')
            lbl.value = f'{hover_col}: {text}'
            # print(properties)
  
    # Convert to WGS 84 and GeoJSON format
    gdf_wgs84 = gdf.to_crs(epsg=4326)
    data = gdf_wgs84.__geo_interface__    
    
    # For each feature in dataset, append colour values
    n_features = len(data['features'])
    colors = n_colors(n_features)
    
    for feature, color in zip(data['features'], colors):
        feature['properties']['style'] = {'color': color, 
                                          'weight': weight, 
                                          'fillColor': color, 
                                          'fillOpacity': 1.0}

    # Get centroid to focus map on
    lon1, lat1, lon2, lat2  = gdf_wgs84.total_bounds
    lon = (lon1 + lon2) / 2
    lat = (lat1 + lat2) / 2
    
    if default_zoom is None:
        
        # Calculate default zoom from latitude of features
        default_zoom = _degree_to_zoom_level(lat1, lat2, margin=-0.5)
    
    # Plot map 
    m = Map(center=(lat, lon), 
            zoom=default_zoom, 
            basemap=basemap, 
            layout=dict(width='800px', height='600px'))
    
    # Add GeoJSON layer to map
    feature_layer = GeoJSON(data=data)
    m.add_layer(feature_layer)
    
    # If a column is specified by `hover_col`, print data from the
    # hovered feature above the map
    if hover_col:        
        lbl = ipywidgets.Label()
        dbg = ipywidgets.Output()        
        feature_layer.on_hover(on_hover)
        display(lbl)
      
    # Display the map
    display(m)



def display_map(x, y, crs='EPSG:4326', margin=-0.5, zoom_bias=0):
    """ 
    Given a set of x and y coordinates, this function generates an 
    interactive map with a bounded rectangle overlayed on Google Maps 
    imagery.        
    
    Last modified: September 2019
    
    Modified from function written by Otto Wagner available here: 
    https://github.com/ceos-seo/data_cube_utilities/tree/master/data_cube_utilities
    
    Parameters
    ----------  
    x : (float, float)
        A tuple of x coordinates in (min, max) format. 
    y : (float, float)
        A tuple of y coordinates in (min, max) format.
    crs : string, optional
        A string giving the EPSG CRS code of the supplied coordinates. 
        The default is 'EPSG:4326'.
    margin : float
        A numeric value giving the number of degrees lat-long to pad 
        the edges of the rectangular overlay polygon. A larger value 
        results more space between the edge of the plot and the sides 
        of the polygon. Defaults to -0.5.
    zoom_bias : float or int
        A numeric value allowing you to increase or decrease the zoom 
        level by one step. Defaults to 0; set to greater than 0 to zoom 
        in, and less than 0 to zoom out.
        
    Returns
    -------
    folium.Map : A map centered on the supplied coordinate bounds. A 
    rectangle is drawn on this map detailing the perimeter of the x, y 
    bounds.  A zoom level is calculated such that the resulting 
    viewport is the closest it can possibly get to the centered 
    bounding rectangle without clipping it. 
    """

    # Convert each corner coordinates to lat-lon
    all_x = (x[0], x[1], x[0], x[1])
    all_y = (y[0], y[0], y[1], y[1])
    all_longitude, all_latitude = transform(Proj(init=crs),
                                            Proj(init='EPSG:4326'), 
                                            all_x, all_y)

    # Calculate zoom level based on coordinates
    lat_zoom_level = _degree_to_zoom_level(min(all_latitude),
                                           max(all_latitude),
                                           margin=margin) + zoom_bias
    lon_zoom_level = _degree_to_zoom_level(min(all_longitude), 
                                           max(all_longitude), 
                                           margin=margin) + zoom_bias
    zoom_level = min(lat_zoom_level, lon_zoom_level)

    # Identify centre point for plotting
    center = [np.mean(all_latitude), np.mean(all_longitude)]

    # Create map
    interactive_map = folium.Map(
        location=center,
        zoom_start=zoom_level,
        tiles="http://mt1.google.com/vt/lyrs=y&z={z}&x={x}&y={y}",
        attr="Google")

    # Create bounding box coordinates to overlay on map
    line_segments = [(all_latitude[0], all_longitude[0]),
                     (all_latitude[1], all_longitude[1]),
                     (all_latitude[3], all_longitude[3]),
                     (all_latitude[2], all_longitude[2]),
                     (all_latitude[0], all_longitude[0])]

    # Add bounding box as an overlay
    interactive_map.add_child(
        folium.features.PolyLine(locations=line_segments,
                                 color='red',
                                 opacity=0.8))

    # Add clickable lat-lon popup box
    interactive_map.add_child(folium.features.LatLngPopup())

    return interactive_map