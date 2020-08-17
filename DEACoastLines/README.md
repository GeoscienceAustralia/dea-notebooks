# DEACoastLines

## Change log

### v0.3.0 (upcoming)

**Outstanding issues**
* Missing oldest contours on eastern side of Fraser Island, QLD (caused by missing path/row 890770)

**Bug fixes**
* In `deacoastlines_statistics.py`: Restored missing contours on western end of Rottnest Island, WA
* In `deacoastlines_statistics.py`: Removed Papua New Guinea territory from data

### v0.2.0 (May 5, 2020)

**Features**
* Add 'uncertainty' column to contour data for pixels with either less than 5 observations or > 0.25 MNDWI standard deviation in more than 50% of years
* Add new `DEACoastLines_utilities.ipynb` notebook containing additional functions for using DEA CoastLines data
* Add `rates_hist` utility function for plotting DEACoastLine statistics data as a histogram based on an interactive selection
* Add ability to modify waterbody mask by providing a vector files of features to add or remove from the mask
* Add new `deacoastlines_summary.py` script for generating continental summary of point statistics based on average values within a buffer of X km of a subset of points. This allows hotspots to be visualised at full zoom out

**Bug fixes**
* In `deacoastlines_generation.py`: Fixed missing grid cell areas by buffering both the input grid cell extent and tide modelling extent by 0.05 degrees (i.e. a total of 0.10 degrees). This ensures that enough tidal modelling points are available for interpolation, and improves tidal modelling consistency between neighbouring grid cells 
* In `deacoastlines_generation.py`: Break script early if grid cell correspondes to 1 or less tidal modelling points, as this makes tidal interpolation impossible
* In `deacoastlines_generation.py`: Increase `dask_chunks` to `{'time': 1, 'x': 2000, 'y': 2000}` for improved data load performance
* In `deacoastlines_statistics.py`: Fixed missing shorelines caused by the waterbody mask by limiting mask to specific waterbody features (`'Aquaculture Area', 'Estuary', 'Watercourse Area', 'Salt Evaporator', 'Settling Pond'` and perennial `'Lakes'`)
* In `deacoastlines_statistics.py`: Fix CRS of exported GeoJSON contours and statistics files by converting to `EPSG:4326`
* In `deacoastlines_statistics.py`: Remove previous zeroing of yearly distance values to 1988. Yearly distances are now relative to the 2018 baseline (e.g. 0 for the 2018 contour), which should be simpler easier to interpret
* In `deacoastlines_statistics.py`: Increase `min_vertices` for contour extraction to 30 to reduce noise
* In `deacoastlines_statistics.py`: Move vector directory creation until after data load, so no directory is created if rasters do not exist

### v0.1.0 (April 1, 2020)

**Features**
* First continental run of DEACoastLines
* Outlier detection now uses a more robust Median Absolute Deviation method

**Bug fixes**
* In `deacoastlines_statistics.py`: Remove mask applied to contour generation due to excessive missing data