# Subpixel waterline extraction 
_Bishop-Taylor et al. 2019, in review_
---


## `subpixel_contours` function

The [`subpixel_contours` function from the `dea_spatialtools.py` script](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Scripts/dea_spatialtools.py#L42-L244) uses `skimage.measure.find_contours` to extract multiple z-value contour lines from a two-dimensional array (e.g. multiple elevations from a single DEM), or one z-value for each array along a specified dimension of a multi-dimensional array (e.g. to map waterlines across time by extracting a 0 NDWI contour from each individual timestep in an xarray timeseries).    
    
Contours are returned as a geopandas.GeoDataFrame with one row per z-value or one row per array along a specified dimension. The     `attribute_df` parameter can be used to pass custom attributes to the output contour features.



## Code examples

[Extracting contour lines](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Frequently_used_code/Contour_extraction.ipynb)

This introductory notebook demonstrates how to use the `subpixel_contours` function to:

* Extract one or multiple contour lines from a single two-dimensional digital elevation model (DEM) and export these as a shapefile
* Optionally include custom attributes in the extracted contour features
* Load in a multi-dimensional satellite dataset from Digital Earth Australia, and extract a single contour value consistently through time along a specified dimension
* Filter the resulting contours to remove small noisy features


## Real-world examples

[Monitoring coastal erosion along Australia's coastline](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Real_world_examples/Coastal_erosion.ipynb)

* Imagery from satellites such as the NASA/USGS Landsat program is available for free for the entire planet, making satellite imagery a powerful and cost-effective tool for monitoring coastlines and rivers at regional or national scale. 
* By identifying and extracting the precise boundary between water and land based on satellite data using the `subpixel_contours` function, it is possible to extract accurate shorelines that can be compared across time to reveal hotspots of erosion and coastal change.

[Modelling intertidal elevation using tidal data](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Real_world_examples/Intertidal_elevation.ipynb)

* Geoscience Australia recently combined 30 years of Landsat data from the Digital Earth Australia archive with tidal modelling to produce the first 3D model of Australia's entire coastline: the National Intertidal Digital Elevation Model or NIDEM (for more information, see Bishop-Taylor et al. 2019 or access the dataset here).
* In this example, we demonstrate a simplified version of the NIDEM method that combines data from the Landsat 5, 7 and 8 satellites with tidal modelling, image compositing and spatial interpolation techniques. 
* Subpixel resolution waterline mapping using the `subpixel_contours` function is used to map the boundary between land and water from low to high tide, with this information then used to generate smooth, continuous 3D elevation maps of the intertidal zone.
