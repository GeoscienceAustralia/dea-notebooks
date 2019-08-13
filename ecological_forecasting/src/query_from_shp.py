import xarray as xr
import geopandas as gpd
def query_from_shp(shp_fpath, start_date, end_date, dask_chunks = 0):
    """
    Uses the extent of a polygon to create a bounding
    box, then generates a query object for the datcube
    """
    #import project area shapefiles
    project_area = gpd.read_file(shp_fpath)

    #convert the shapefile to GDA94 lat-long coords so we can query dc_load using lat long
    project_area['geometry'] = project_area['geometry'].to_crs(epsg=4283)

    #find the bounding box that contains all the queried projects
    x = project_area.total_bounds
    #longitude
    ind = [0,2]
    extent_long = x[ind]  
    extent_long = tuple(extent_long)
    #latitude
    ind1 = [1,3]
    extent_lat = x[ind1] 
    extent_lat = tuple(extent_lat)

    #datacube query is created
    query = {'time': (start_date, end_date),}
    query['x'] = extent_long
    query['y'] = extent_lat
    if dask_chunks != 0:
        query['dask_chunks']= {'x': dask_chunks, 'y': dask_chunks} #divide query into chunks to save memory
        return query
    return query