 # read in WOs geotiff, output Vector 

# 1. create binary arrays for classed of interest: 1)water and 2)Not Analysed
# 2. conduct binary errosion and dialation to remove single pixles/big gaps between datatypes
#     - B) conduct fill on water to remove single pixle holes?
#     - C) conduct 1 pixle buffer of no-data class? (unsure if should be latter in workflow)
# 3. vectorise 
# 4. simplify shapes to remove complixity
# 5. join both data types back together as one Geopandas Geodataframe (container for sapely objects with projection imformation)
# 6. export an a single sapefile with attributes intact. 


#import modules
import xarray as xr
import pandas as pd
import geopandas as gp
import fiona
from fiona.crs import from_epsg
import rasterio.features
from shapely.geometry import Polygon, shape, asShape, mapping
from scipy import ndimage
 
 # vectorise the arrays
def vectorise_data(xarrayDataArray, input_crs, label='Label'):
    """this module takes an Xarray DataArray and vectorises it as shapely geometries then puts them in a Geopandas Geodataframe

    Input
    xarrayDataArray: an Xarray DataArray with boolean values (1,0) with 1 or True equal to the areas that will be turned into vectors
    Label: default 'Label', String, the data label that will be added to each geometry in geodataframe
    input_crs: the CRS the input raster is in. this needs to be provided to the geopandas geodataframe becasue shapey geometries have not projection info
    
    output
    Geodataframe containing shapely geometies with data type lable in a series called attribute
    """

    vector  =  rasterio.features.shapes(
        xarrayDataArray.data.astype('float32'),
        mask=xarrayDataArray.data.astype('float32') == 1, #this defines which part of array becomes polygons
        transform=wos_dataset.transform)

    vectored_data = list(vector) #put tupple output in list

    # Extract the polygon coordinates from the list
    polygons = [polygon for polygon, value in vectored_data]
    #create empty list for lables
    labels = []
    # put in labels
    for i in polygons:
        labels.append(label) # create a list with the data label type 

    # Convert polygon coordinates into polygon shapes
    polygons = [shape(polygon) for polygon in polygons]

    # Create a geopandas dataframe populated with the polygon shapes
    data_gdf = gp.GeoDataFrame(data={'attribute': labels},
                       geometry=polygons,
                       crs=input_crs)

    return(data_gdf)
    

"""Define Geotiff filepath aand open"""

geotiff_path = 'smol_eucambene.tif'

geotiff_wos = xr.open_rasterio(geotiff_path)
wos_dataset = geotiff_wos.to_dataset('band')
wos_dataset = wos_dataset.rename({1:'wo'})


# grab crs from input tiff
dataset_crs = from_epsg((wos_dataset.crs)[11:])


"""Defining the three 'groups':
a) Water: where water is observed. Bit value 128
b) unspoken 'dry'. this is not vectorised and is left and transparent layer. bit values: 1 (no data) 2 (Contiguity)
c) Not_analysed: every masking applied to the data except terrain shadow. bit values: composed of Everyting else,"""


# 1 create binary arrays for two groups of interest 
water_vals = (wos_dataset.wo == 128) #water only has 128 water observations


#here we used reversed logic to turn all pixles that should be 'not analysed' to a value of 3. is is easier to list the 4 classes that are passed to the unlabled 'dry' class
not_analysed = wos_dataset.wo.where(((wos_dataset.wo ==0)|(wos_dataset.wo ==1)|(wos_dataset.wo ==8)
                                     |(wos_dataset.wo ==2)|(wos_dataset.wo ==128)|(wos_dataset.wo ==130)|(wos_dataset.wo ==142)), 3) 
not_analysed = not_analysed.where((not_analysed==3), 0) #now keep the 3 values and make everyting else 0


# 2 conduct binary errosion and closing to remove single pixles
erroded_water = xr.DataArray(ndimage.binary_erosion(water_vals, iterations=1 ).astype(water_vals.dtype), coords=water_vals.coords)
erroded_not_analysed = xr.DataArray(ndimage.binary_erosion(not_analysed, iterations=3 ).astype(not_analysed.dtype), coords=not_analysed.coords)

# dialating cloud 3 times after erroding 2, to create small overlap and iliminate gaps in data
dialated_water = xr.DataArray(ndimage.binary_dilation(erroded_water, iterations=2 ).astype(water_vals.dtype), coords=water_vals.coords)
dialated_not_analysed = xr.DataArray(ndimage.binary_dilation(erroded_not_analysed, iterations=(3) ).astype(not_analysed.dtype), coords=not_analysed.coords)

#Apply Vectorisation

notAnalysedGPD = vectorise_data(dialated_not_analysed, dataset_crs, label='Not_analysed')
WaterGPD = vectorise_data(dialated_water, dataset_crs, label='Water')

#conduct simplification

#change to 'epsg:3577' prior to simplifiying to insure consistent results
notAnalysedGPD = notAnalysedGPD.to_crs('epsg:3577')
WaterGPD = WaterGPD.to_crs('epsg:3577')

# Simplify

#Run simplification with 10 tollerance for water and 15 for Not Analysed
simplifyed_water = WaterGPD.simplify(10)

simplifyed_notAnalysed = notAnalysedGPD.simplify(15)

#Put simplified shapes back into in a dataframe 
simple_waterGPD = gp.GeoDataFrame(geometry=simplifyed_water,
                       crs=from_epsg('3577'))

simple_notAnalysedGPD = gp.GeoDataFrame(geometry=simplifyed_notAnalysed,
                       crs=from_epsg('3577'))


#add attribute lables back in
simple_waterGPD['attribute'] = WaterGPD['attribute']

simple_notAnalysedGPD['attribute'] = notAnalysedGPD['attribute']

# 6 Join together as One Geopandas Geodataframe
All_classes = gp.GeoDataFrame( pd.concat([simple_waterGPD,simple_notAnalysedGPD],ignore_index=True),
                                 crs=simple_notAnalysedGPD.crs)

"""If desiered Write to file as shapefile with same name as original Geotiff"""

# # Save the polygons to a shapefile


# schema = {
#     'geometry': 'Polygon',
#     'properties': {
#         'attribute':'str'
#     }
# }

# # Generate our dynamic filename
# FileName = f'{geotiff_path[:-4]}.shp'

# #create file and save
# with fiona.open(FileName,
#                 "w",
#                 crs=from_epsg(3577),
#                 driver='ESRI Shapefile',
#                 schema=schema) as output:
#     for ix, poly in All_classes.iterrows():
#         output.write(({
#                 'properties': {
#                 'attribute': poly['attribute']
#                 },
#                 'geometry': mapping(shape(poly['geometry']))
#                 }))