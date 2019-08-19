# Utils
import json
from skimage import exposure
import numpy as np
import osr
import ogr
from geopy.geocoders import GoogleV3


def lat_lon_to_epsg(lat_max, lon_min):
    return str(int(32700 - round((45 + lat_max) / 90, 0) * 100 + round((183 + lon_min) / 6, 0)))


def three_band_image(ds, bands, time=0, figsize=[10, 10], projection='projected'):
    '''
    three_band_image takes three spectral bands and plots them on the RGB bands of an image.

    Inputs:
    ds -   Dataset containing the bands to be plotted
    bands - list of three bands to be plotted

    Optional:
    time - Index value of the time dimension of ds to be plotted
    figsize - dimensions for the output figure
    projection - options are 'projected' or 'geographic'. To determine if the image is in degrees or northings
    '''
    t, y, x = ds[bands[0]].shape
    rawimg = np.zeros((y, x, 3), dtype=np.float32)
    for i, colour in enumerate(bands):
        rawimg[:, :, i] = ds[colour][time].values
    rawimg[rawimg == -9999] = np.nan
    img_toshow = exposure.equalize_hist(rawimg, mask=np.isfinite(rawimg))

    return img_toshow

##---
def transform_from_wgs(getLong, getLat, EPSGa):
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)

    target = osr.SpatialReference()
    target.ImportFromEPSG(EPSGa)

    transform = osr.CoordinateTransformation(source, target)

    point = ogr.CreateGeometryFromWkt("POINT (" + str(getLong) + " " + str(getLat) + ")")
    point.Transform(transform)
    return [point.GetX(), point.GetY()]

##--

def transform_from_wgs_poly(geo_json,EPSGa):

    polygon = ogr.CreateGeometryFromJson(str(geo_json))

    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)

    target = osr.SpatialReference()
    target.ImportFromEPSG(EPSGa)

    transform = osr.CoordinateTransformation(source, target)
    polygon.Transform(transform)

    return eval(polygon.ExportToJson())


def load_config_extents(file):
    config = json.load(open(file))
    lon_min, lon_max = config['lon']
    lat_min, lat_max = config['lat']
    rectangle = [
        [lat_max, lon_min],
        [lat_max, lon_max],
        [lat_min, lon_max],
        [lat_min, lon_min],
        [lat_max, lon_min]]
    return [[lon_min, lon_max, lat_min, lat_max], rectangle]


def transform_to_wgs(getLong, getLat, EPSGa):
    source = osr.SpatialReference()
    source.ImportFromEPSG(EPSGa)

    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)

    transform = osr.CoordinateTransformation(source, target)

    point = ogr.CreateGeometryFromWkt("POINT (" + str(getLong[0]) + " " + str(getLat[0]) + ")")
    point.Transform(transform)
    return [point.GetX(), point.GetY()]



def find_mining_tenement(mine_id):
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    file_path = 'data/Mining_Tenements_Centroids_WGS.shp' 
    dataSource = driver.Open(file_path, 0) # 0 means read-only. 1 means writeable.
    if not dataSource:
        print ('missing source data ')
        return
    
    layer = dataSource.GetLayer()
    layer.SetAttributeFilter("fmt_tenid = '" + mine_id + "'")
    
    for mine in layer:
        point = mine.GetGeometryRef()
    
    return [point.GetY(),point.GetX()]

def find_address(address_text):
    
    g = GoogleV3()
    location = g.geocode(address_text)
    
    return [location.latitude,location.longitude]