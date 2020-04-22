# DEACoastLines

## Change log

### v0.2.0 (upcoming)

**Features**
* Added 'uncertainty' column to contour data for pixels with either less than 5 observations or > 0.25 MNDWI standard deviation in over 75% of years

**Bug fixes**
* Fixed missing shorelines caused by the estuary mask by limiting mask to specific waterbody features ('Aquaculture Area', 'Estuary', 'Watercourse Area', 'Salt Evaporator', 'Settling Pond' and perennial 'Lakes')
* Fixed missing grid cell areas by buffering both the input grid cell extent and tide modelling extent by 0.05 degrees (i.e. a total of 0.10 degrees)
* Fix CRS of exported GeoJSON by convert to EPSG:4326)


### v0.1.0 (April 1, 2020)

**Features**
* First continental run of DEACoastLines
* Outlier detection now uses a more robust Median Absolute Deviation method