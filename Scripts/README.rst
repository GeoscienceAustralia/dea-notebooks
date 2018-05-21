=============================
Scripts
=============================

This folder contains examples of python code that demonstrates the use of functions and tools suitable for use in the DEA environment. The following functions are currently included in Python scripts for loading into notebooks:

DEADataHandling.py: handling data using DEA functionality (i.e. dc.load or xarrays)
     - **load_nbarx**: Loads NBAR (Nadir BRDF Adjusted Reflectance) or NBAR-T (terrain corrected NBAR) data for a sensor, masks using pixel quality (PQ), then optionally filters out terrain -999s (for NBAR-T)
     - **load_sentinel**: Loads a Sentinel granule product and masks using PQ
     - **load_clearlandsat**: Loads time series of clear Landsat observations from the entire archive
     - **tasseled_cap**: Computes tasseled cap wetness, greenness and brightness bands from a six band xarray dataset
     - **dataset_to_geotiff**: Writes a multi-band geotiff for one xarray timeslice, or for a single composite image
     - **open_polygon_from_shapefile**: Imports a shapefile and converts to a datacube geometry object
     - **write_your_netcdf**: Writes an xarray dataset or array to a NetCDF file
     
DEAPlotting.py: plotting DEA data (e.g. xarrays)
     - **three_band_image**: Takes three spectral bands and plots them on the RGB bands of an image
     - **three_band_image_subplots**: Takes three spectral bands and multiple time steps, and plots them on the RGB bands of an image
     - **animated_timeseries**: Takes an xarray time series and exports an animation showing landscape change across time
     - **animated_fade**: Takes two single-timestep xarray datasets and exports a fading/transitioning animation

BandIndices.py: calculating remote sensing band indices
     - **calculate_indices**: Computes a set of indices (including NDVI, GNDVI, NDWI, NDMI) from an xarray dataset
     - **geological_indices**: Computes a set of geological remote sensing indices (including CMR, FMR, IOR) from an xarray dataset
     
SpatialTools.py: Rasters/shapefile manipulation functions that do not rely on DEA (i.e. no dc.load or xarrays)
     - **rasterize_vector**: Rasterize a vector file and return as an array
     - **layer_extent**: Computes min and max extents from GDAL layer features
     - **indices_to_coords**: Takes lists of x and y array indices and converts them to equivelent spatial x and y coordinates
     - **coords_to_indices**: Takes lists of x and y coordinates and converts to equivelent raster array cell indices
     - **raster_randomsample**: Generate a set of n random points within cells of a raster that contain data
     - **array_to_geotiff**: Create a single band GeoTIFF file with data from an array
     - **reproject_to_template**: Reprojects a raster to match the extent, cell size, projection and dimensions of a template raster using GDAL
         
ClassificationTools.py: classifying remote sensing imagery using classifiers and machine learning
     - **randomforest_train**: Extracts training data from xarray dataset for multiple training shapefiles
     - **randomforest_classify**: Performs classification of xarray dataset using pre-trained random forest classifier, and export classified output to a geotiff
     - **randomforest_eval**: Takes a set of training labels and training samples, and plots OOB error against a range of classifier parameters to explore how parameters affect classification
    
    
    


.. toctree::
   :maxdepth: 1
