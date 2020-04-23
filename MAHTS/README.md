# DEACoastLines

## Change log

### v0.2.0 (upcoming)

**Features**
* Add 'uncertainty' column to contour data for pixels with either less than 5 observations or > 0.25 MNDWI standard deviation in over 75% of years
* Add new `DEACoastLines_utilities.ipynb` notebook containing additional functions for using DEA CoastLines data
* Add `rates_hist` utility function for plotting DEACoastLine statistics data as a histogram based on an interactive selection
* Add ability to modify waterbody mask by providing a vector files of features to add or remove from the mask

**Bug fixes**
* `deacoastlines_generation.py`: Fixed missing grid cell areas by buffering both the input grid cell extent and tide modelling extent by 0.05 degrees (i.e. a total of 0.10 degrees). This ensures that enough tidal modelling points are available for interpolation, and improves tidal modelling consistency between neighbouring grid cells 
* `deacoastlines_generation.py`: Break script early if grid cell correspondes to 1 or less tidal modelling points, as this makes tidal interpolation impossible
* `deacoastlines_generation.py`: Increase `dask_chunks` to `{'time': 1, 'x': 2000, 'y': 2000}` for improved data load performance
* `deacoastlines_statistics.py`: Fixed missing shorelines caused by the waterbody mask by limiting mask to specific waterbody features (`'Aquaculture Area', 'Estuary', 'Watercourse Area', 'Salt Evaporator', 'Settling Pond'` and perennial `'Lakes'`)
* `deacoastlines_statistics.py`: Fix CRS of exported GeoJSON contours and statistics files by converting to `EPSG:4326`
* `deacoastlines_statistics.py`: Remove previous zeroing of yearly distance values to 1988. Yearly distances are now relative to the 2018 baseline (e.g. 0 for the 2018 contour), which should be simpler easier to interpret
* `deacoastlines_statistics.py`: Update all time coastal buffer to 1200 m (from 1000 m) to prevent lost contours in extremely dynamic regions

* `deacoastlines_statistics.py`: Increase `min_vertices` for contour extraction to 30 to reduce noise
* `deacoastlines_statistics.py`: Move vector directory creation until after data load, so no directory is created if rasters do not exist

### v0.1.0 (April 1, 2020)

**Features**
* First continental run of DEACoastLines
* Outlier detection now uses a more robust Median Absolute Deviation method

**Bug fixes**
* `deacoastlines_statistics.py`: Remove mask applied to contour generation due to excessive missing data