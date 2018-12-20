=======
Scripts
=======

This folder contains examples of python code that demonstrates the use of functions and tools suitable for use in the DEA environment. The code examples provided here can be found in the `dea-notebooks Github repository <https://github.com/GeoscienceAustralia/dea-notebooks>`_. Note that these functions have been developed by DEA users, not the DEA development team, and so are provided without warranty. If you find an error or bug in the functions, please either create an Issue in the Github repository, or fix it yourself and create a Pull request to contribute the updated function back into the repository (See the repository README for instructions on creating a Pull request).

The **FlexibleStats.py** script is for use in conjunction with DEA stats to create products using non-sequential dates, further information is located within the file.

The following functions are currently included in Python scripts for loading into notebooks:

DEADataHandling.py: handling data using DEA functionality (i.e. dc.load or xarrays)
     - **load_nbarx**: Loads NBAR (Nadir BRDF Adjusted Reflectance) or NBAR-T (terrain corrected NBAR) data for a sensor, masks using pixel quality (PQ), then optionally filters out terrain -999s (for NBAR-T)
     - **load_sentinel**: Loads a Sentinel granule product and masks using PQ
     - **load_clearlandsat**: Loads a time series of Landsat observations from multiple sensors (ls5, ls7, ls8) with less than xx% cloud or nodata
     - **load_clearsentinel2**: Loads a time series of Sentinel 2 observations from multiple sensors (s2a, s2b) with less than xx% cloud or nodata
     - **dataset_to_geotiff**: Writes a multi-band geotiff for one xarray timeslice, or for a single composite image
     - **open_polygon_from_shapefile**: Imports a shapefile and converts to a datacube geometry object
     - **write_your_netcdf**: Writes an xarray dataset or array to a NetCDF file
     
DEAPlotting.py: plotting DEA data (e.g. xarrays)
     - **three_band_image**: Takes three spectral bands and plots them on the RGB bands of an image
     - **three_band_image_subplots**: Takes three spectral bands and multiple time steps, and plots them on the RGB bands of an image
     - **animated_timeseries**: Takes an xarray time series and exports an animation showing landscape change across time
     - **animated_doubletimeseries**: Takes two xarray datasets and exports a two panel animation
     - **animated_timeseriesline**: Plots a pandas dataframe as a line graph next to an xarray dataset
     - **plot_WOfS**: Use the DEA WOfS color ramp to plot WOfS percentage data

BandIndices.py: calculating remote sensing band indices
     - **calculate_indices**: Computes a set of indices (including NDVI, GNDVI, NDWI, NDMI) from an xarray dataset
     - **geological_indices**: Computes a set of geological remote sensing indices (including CMR, FMR, IOR) from an xarray dataset
     - **tasseled_cap**: Computes tasseled cap wetness, greenness and brightness bands from an xarray dataset
     
SpatialTools.py: Rasters/shapefile manipulation functions that do not rely on DEA (i.e. no dc.load or xarrays)
     - **rasterize_vector**: Rasterize a vector file and return as an array
     - **contour_extract**: Extract contour lines from a two-dimensional array and optionally export contour line shapefile
     - **indices_to_coords**: Takes lists of x and y array indices and converts them to equivelent spatial x and y coordinates
     - **coords_to_indices**: Takes lists of x and y coordinates and converts to equivelent raster array cell indices
     - **raster_randomsample**: Generate a set of n random points within cells of a raster that contain data
     - **array_to_geotiff**: Create a single band GeoTIFF file with data from an array
     - **reproject_to_template**: Reprojects a raster to match the extent, cell size, projection and dimensions of a template raster using GDAL
         
ClassificationTools.py: classifying remote sensing imagery using classifiers and machine learning
     - **randomforest_train**: Extracts training data from xarray dataset for multiple training shapefiles
     - **randomforest_classify**: Performs classification of xarray dataset using pre-trained random forest classifier, and export classified output to a geotiff
     - **randomforest_eval**: Takes a set of training labels and training samples, and plots OOB error against a range of classifier parameters to explore how parameters affect classification
    
SignificanceTests.py: per-pixel hypothesis testing  
     - **significance_tests**: Given two xarray dataarrays from non-overlapping time-periods, conducts either a t-test or a Levene's test to determine if the mean or variance are equal, respectively    
     
TasseledCapTools.py: a set of python functions to use with the outputs of tasseled cap transforms
     - **thresholded_tasseled_cap**: Computes thresholded tasseled cap wetness, greenness and brightness bands from a six band xarray dataset
     - **pct_exceedance_tasseled_cap**: Counts the number of thresholded tasseled cap scenes per pixel and divides by the number of tasseled cap scenes per pixel

RainfallTools.py: load rainfall from BoM rainfall grids
     - **load_rainfall**: Loads gridded rainfall data and fixes offset in underlying BoM data

FileDialogs.py: A set of file dialog widgets for file paths for opening or saving files.
     - **SaveFileButton**:creates a button to save your file
     - **SelectFileButton**:creates a button to select one file
     - **SelectFilesButton**:SelectFilesButton returns a list of file paths (strings)
.. toctree::
   :maxdepth: 1
