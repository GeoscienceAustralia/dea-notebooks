
import xarray as xr
from multiprocessing import Pool
import geopandas as gpd
import shapely
import rasterio.features
import numpy as np

#USER INPUTS
cpus=4
mask_dir = 'data/nmdb_LSandOEH_mask_commission_cleaned.tif'
directory = "results/nmdb/"
input_suffix = "_multithreshold_65Thres"
output_suffix = "_LSandOEHandCommission_masked"

#file paths setup
x = range(1987,2019,1)
years = []
for i in x:
    nextyear = str(i + 1)[2:]
    y = str(i) + "_" + nextyear
    years.append(str(y))
years =  [e for e in years if e not in ('2011_12', '2012_13')]
years.sort()

inputs=[]
for year in years:
    inputs.append(directory+"nmdb_"+year+"/nmdb_Summer" + year + input_suffix + ".tif")

#masking function
def clip_tiff(tif):
    print("working on year: " + tif[26:-4])
    
    #open datasets
    a = xr.open_rasterio(tif).squeeze()
    mask = xr.open_rasterio(mask_dir).squeeze()

    #mask with lsandoeh mask
    b = a.where(mask).rename('irrigated_area')
    b.attrs = a.attrs

     #Convert to polygons and clean by area
    vectors = rasterio.features.shapes(source=b.data.astype('int16'),
                                       mask=np.isfinite(b.data),
                                       transform=b.transform)
    
    vectors = list(vectors)
    polygons = [polygon for polygon, value in vectors]
    values = [value for polygon, value in vectors]
    polygons = [shapely.geometry.shape(polygon) for polygon in polygons]

    # Create a geopandas dataframe populated with the polygon shapes
    gdf = gpd.GeoDataFrame(data={'DN': values},
                           geometry=polygons,
                           crs={'init' :'epsg:3577'})
    
    gdf['area'] = gdf['geometry'].area
    gdf = gdf[gdf.area>100000]
    gdf.to_file(tif[:-27]+ "_Irrigated" +output_suffix+ ".shp")

# clip_tiff(inputs[0])
pool = Pool(cpus)    
pool.map(clip_tiff, inputs) 
    

