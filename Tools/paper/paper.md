---
title: "dea-tools: geospatial analysis of satellite data using Digital Earth Australia, Open Data Cube, and Xarray."
tags:
  - Python
  - Earth observation
  - Remote sensing
  - Xarray
  - Open Data Cube
  - Satellite data
authors:
  - name: Chad Burton
    corresponding: true
    orcid: 0000-0003-3048-8484
    affiliation: 1
affiliations:
  - name: Geoscience Australia, Australia
    index: 1
    ror: 04ge02x20

date: 14 October 2025
bibliography: paper.bib
---

# Summary

`dea-tools` is an open-source Python package for geospatial analysis of satellite data using Digital Earth Australia, [Open Data Cube](https://www.opendatacube.org/) (ODC) and `xarray` [@Hoyer_xarray_N-D_labeled_2017]. It provides a broad set of utilities for loading, visualising, transforming, and analysing Earth Observation (EO) data across space and time

The package includes tools for:

* **Data handling**: Load and combine DEA data products, manage projections and resolutions.
* **Visualisation**: Create static and interactive maps, RGB plots, and animations.
* **Remote sensing indices**: Calculate band indices such as NDVI, NDWI, and more.
* **Spatial and temporal analysis**: Apply raster/vector operations, extract contours, compute temporal stats, and model change over time.
* **Machine learning and segmentation**: Train and apply classifiers, or run image segmentation workflows.
* **Parallel processing**: Set up Dask clusters for scalable processing of large datasets.
* **Domain-specific tools**: Analyse coastal change, intertidal zones, land cover, wetland and waterbody dynamics, and climate datasets. 

# Statement of need

Satellite remote sensing offers an unparalleled resource for

# Features

## Analytical tools native to Xarray

Flexible and powerful functionality for scientific analysis with xarray objects:

- Extracting time series statistics, using the module `dea-tools.temporal`:
    * Generic summary statistics on any time series with `temporal_statistics`
    * Phenology with `xr_phenology`
    * Linear regression with `xr_regression`
- Validation tools within `dea-tools.validation`:
    * Compute common statistical metrics with `eval_metric`
    * Generate random points over an xarray object with `xr_random_sampling`
- Spatial analysis tools within `dea-tools.spatial`:
    * Vectorise xarray.DataArrays into geopandas.GeoDataFrames with `xr_vectorise`
    * Rasterize geopandas.GeoDataFrames into xarray.DataArrays with `xr_rasterize`
    * Extract subpixel contours from xarray.DataArrays with `subpixel_contours`
    * Interpolate point data stored in a geopandas.GeoDataFrame into an xarray.DataArray with `xr_interpolate`
- Xarray wrappers for the full machine learning pipeline in in `dea-tools.classification`:
    * prepare data for ML predictions with `sklearn_flatten` and `sklearn_unflatten`
    * Fit models with `fit_xr`
    * ML predictions with `predict_xr`
    * Handle spatial autocorrelation in cross-validation workflows with `spatial_train_test_split` and `SKCV` (spatial k-fold cross validation)

## Plotting

The `dea-tools.plotting` library has extensive functionality for generating beautiful imagery from xarray objects.
- RGB plots for true and false colour composite images with `rgb`
- Highly customisable animations with `xr_animation`

## Integration with Open Data Cube libraries

dea-tools works naively with odc-geo

# Acknowledgements

Thanks

# References
