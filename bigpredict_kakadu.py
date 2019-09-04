#Run the kMeans tree clustering on *all* of Kakadu and save the 
#results as a file that we can load on VDI (or other).
#Will require a big memory node on raijin, because the code is pretty
#dumb and not using dask or anything like that. All of Kakadu will require
#50+ GB of memory just for the first dc.load()


#imports
import numpy as np
import datacube
import matplotlib.pyplot as plt
import radar_functions as rf
import radar_gmm as rg
import fiona
from datacube.utils import geometry
import rasterio.features

import xarray as xr

import pickle

# Import external functions from dea-notebooks
import sys
sys.path.append('./10_Scripts/')
import DEAPlotting, DEADataHandling

#load the 'Kakadu' polygon from the Ramsar wetlands shapefile and set up a query to download data for it
shp_path='/g/data/r78/rjd547/Ramsar_Wetlands/shapefiles/Ramsar_exploded3.shp'
shapes=fiona.open(shp_path,'r')

crs=geometry.CRS(shapes.crs_wkt)

#Kakadu is at index 12 in this shapefile
shape=shapes[12]
shape_geometry=shape['geometry']
geom=geometry.Geometry(shape_geometry,crs=crs)

query = {'geopolygon': geom,
         'time': ('2016-09-01', '2019-06-01')
         }

dc = datacube.Datacube(config='radar.conf')

#make the input for the kmeans tree all in one go. Hopefully the spatial filtering doesn't make this
#take forever
print("Loading filtered SAR images...")

with open("mamukala_scaling_factors.pkl","rb") as f: scaler = pickle.load(f)

all_in = rf.bulknorm_SAR_ds(np.log(rf.load_cleaned_SAR(query,dc,drop_bad_scenes=False)))

print("Images loaded and input prepared. Loading fitted KMeans tree model...")

with open("mamukala_full_fit.pkl","rb") as f: ktree = pickle.load(f)

print("Fit complete. Predicting pixel classes...")

ktr_out = ktree.predict_dataset(all_in)

print("Class predictions ready. Saving to netCDF...")

#add the units back onto the output so netCDF stops complaining
ktr_out.time.attrs['units']=all_in.time.attrs['units']
ktr_out.x.attrs['units']=all_in.x.attrs['units']
ktr_out.y.attrs['units']=all_in.y.attrs['units']


#save the output
epsg3577 = geometry.CRS('EPSG:3577')
DEADataHandling.write_your_netcdf(ktr_out,'cover_classes',"kakadu_sar.nc",epsg3577)

print("Saved. Exiting...")

