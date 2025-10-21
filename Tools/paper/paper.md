---
title: "dea-tools: Geospatial analysis of satellite data using Xarray, the Open Data Cube, and Digital Earth Australia"
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
  - name: Robbi Bishop-Taylor
    orcid: 0000-0002-1533-2599
    affiliation: 1
  - name: Bex Dunn
    affiliation: 1
    orcid: 0000-
  - name: Claire Phillips
    affiliation: 1
    orcid: 0009-0003-9882-9131
  - name: Caitlin Adams
    affiliation: 1
    orcid: 0000-
  - name: Gianluca Scortechini
    affiliation: 1
    orcid: 0000-0002-0149-4028
  - name: Sean Chua
    affiliation: 1
    orcid: 0000-
  - name: Vanessa Newey
    affiliation: 1
    orcid: 0000-0003-3705-5665
  - name: Margaret Harrison
    affiliation: 1
    orcid: 0000-
  - name: Jenna Guffogg
    affiliation: 1
    orcid: 0000-0003-2804-9554
  - name: Claire Krause
    affiliation: 1
    orcid: 0000-
  - name: James Miller
    affiliation: 1
    orcid: 0000-
affiliations:
  - name: Geoscience Australia, Australia
    index: 1
    ror: 04ge02x20

date: 14 October 2025
bibliography: paper.bib
---

# Summary

`dea-tools` is an open-source Python library that provides a comprehensive set of tools for analysing, visualising, and modelling geospatial and Earth observation data represented as `xarray` objects. Originally developed to support [Digital Earth Australia (DEA)](https://knowledge.dea.ga.gov.au/) workflows, `dea-tools` has evolved into a general-purpose library for use with any geospatial dataset. The package includes utilities for spatial and temporal analysis, remote sensing index calculation, machine learning, interactive visualisation, and integrates seamlessly with the Python geospatial stack (e.g. `xarray` [@Hoyer_xarray_N-D_labeled_2017], `geopandas` [@kelsey_jordahl_2020_3946761], and `dask` [@dask]). Distributed as a pip-installable environment, `dea-tools` includes JupyterLab and related dependencies, providing a fully managed platform for scientific geospatial analysis across computing environments. Embedded within the broader `dea-notebooks` [@krause2021dea] repository, the package is supported by extensive documentation and example Jupyter notebooks demonstrating the use of `dea-tools` functionality. Together, `dea-tools` and `dea-notebooks` support reproducible and scalable Earth observation science with Python.

# Statement of need

Modern Earth observation workflows often involve complex, multi-temporal, and multi-resolution datasets that demand integrated tools for efficient loading, pre-processing, visualisation, and analysis. While foundational libraries such as `xarray`, `geopandas`, and `dask` provide the building blocks, implementing efficient and scalable analysis workflows and processing pipelines still requires substantial coding effort. The `dea-tools` Python library addresses this gap by providing a curated suite of well-documented functions that streamline common geospatial tasks and integrate seamlessly with the Python geospatial stack.

`dea-tools` is a comprehensive, open-source toolkit for analysing and interpreting geospatial and Earth observation data, primarily represented as `xarray` objects. Originally developed by DEA to support national-scale satellite data analysis, `dea-tools` has evolved into a flexible and general-purpose library that supports a wide range of geospatial workflows. It can be deployed across platforms and supports both gridded datasets (e.g. satellite imagery) and vector datasets (e.g. shapefiles or GeoJSON), whether accessed from cloud-based catalogues via Spatio-Temporal Asset Catalog (STAC) or stored locally.

A major advantage of `dea-tools` is that it comes bundled with all essential dependencies for scientific geospatial analysis. These include [JupyterLab](https://jupyter.org/), Jupyter notebooks, `xarray`, `geopandas`, `NumPy` [@harris2020array], `dask`, and many other libraries from the Python geospatial ecosystem. When deployed within a virtual environment, `dea-tools` provides a ready-to-use and pre-configured platform for geospatial analysis, eliminating the need for manual setup or dependency management. This design lowers the barrier to entry for new users by offering a self-contained environment for exploration, visualisation, and large-scale satellite data processing.

`dea-tools` enables users to:

* Load, combine, and manage satellite or model datasets – including but not limited to DEA products – while handling reprojection and resolution harmonisation;
* Conduct spatial and temporal analyses directly on `xarray` objects (e.g., extracting temporal statistics, linear regression, and interpolation);
* Apply a large curated list of remote sensing indices such as Normalised Difference Vegetation Index (NDVI), Normalised Difference Water Index (NDWI), etc.;
* Perform machine learning and segmentation workflows on geospatial datasets using built-in tools for training, fitting, and prediction that integrates seamlessly with `xarray`;
* Generate publication-quality visualisations and animations for both static and time-series data;
* Convert between raster and vector formats with utilities that bridge `xarray` and `geopandas`;
* Apply domain-specific tools to analyse coastal change, intertidal zones, land cover, wetland and waterbody dynamics, and climate datasets;
* Generate Cloud-Optimised GeoTIFF (COG) continental mosaics and create VRTs with styling included for effortless visualisation in GIS software; this functionality is provided by the [`mosaics` sub-module](https://github.com/GeoscienceAustralia/dea-notebooks/blob/stable/Tools/dea_tools/mosaics/README.md), which accesses product tiles directly from S3 without requiring `datacube` or `STAC`.

The broader `dea-notebooks` repository, which includes `dea-tools`, provides extensive Jupyter notebook based documentation. This includes concise how-to guides for specific tasks as well as longer, real-world application examples. These resources feature end-to-end workflows that demonstrate how to acquire satellite data via [odc-stac](https://github.com/opendatacube/odc-stac), process it using `dea-tools`, and visualise outputs interactively within JupyterLab. Together, `dea-tools` and `dea-notebooks` offer a reproducible, scalable, and fully managed framework for geospatial analysis in Python, bridging the gap between foundational geospatial libraries and applied Earth observation research.

# Features

The following is a non-exhaustive overview of key functionality available in `dea-tools`. Each function is supported by an accompanying Jupyter notebook that demonstrates its usage.

## Data handling

Tools for loading and manipulating DEA satellite data, as well as data from other geospatial providers, are available in the [`dea-tools.datahandling`](https://knowledge.dea.ga.gov.au/notebooks/Tools/gen/dea_tools.datahandling/):

- `load_ard`: Load and combine multiple Geoscience Australia Landsat, Sentinel-2, or Sentinel-1 Analysis Ready Data products using `odc-stac`. Optional features include pixel quality filtering, cloud and contiguity masking, and dropping time steps with a high proportion of poor-quality (e.g. cloudy or shadowed) pixels.
- `load_reproject`:  Load and reproject all or part of a raster dataset (stored either locally or remotely) to match the coordinate reference system and/or resolution of another dataset.

## Spatio-temporal analysis 

Flexible and powerful tools for scientific analysis with `xarray` objects:

- Extracting time series statistics, using the module [`dea-tools.temporal`](https://knowledge.dea.ga.gov.au/notebooks/Tools/gen/dea_tools.temporal/):
    * Generic summary statistics on any time series with `temporal_statistics`;
    * Land surface phenology with `xr_phenology`;
    * Linear regression with `xr_regression`.
- Spatial analysis tools within [`dea-tools.spatial`](https://knowledge.dea.ga.gov.au/notebooks/Tools/gen/dea_tools.spatial/):
    * Vectorise `xarray.DataArrays` into `geopandas.GeoDataFrames` with `xr_vectorize`;
    * Rasterise `geopandas.GeoDataFrames` into `xarray.DataArrays` with `xr_rasterize` ;
    * Extract detailed contours from `xarray.DataArrays` at subpixel resolution using `subpixel_contours`;
    * Interpolate point data stored in a `geopandas.GeoDataFrame` into an `xarray.DataArray` with `xr_interpolate`.

![`dea-tools` enables easy transitions between `xarray` and `geopandas` with the `xr_rasterize` and `xr_vectorize` functions. Location: Menindeee Lakes, New South Wales.\label{fig:raster-vector}](figures/rasterize_vectorize.png)

## Machine learning 

`dea-tools` provides a number of functions for simplifying machine learning (ML) with `xarray`:

- `xarray` wrappers for the full ML pipeline in [`dea-tools.classification`](https://knowledge.dea.ga.gov.au/notebooks/Tools/gen/dea_tools.classification/):
    * Prepare data for ML predictions with `sklearn_flatten` and `sklearn_unflatten`;
    * Fit models with `fit_xr`;
    * ML predictions with `predict_xr`.
    * Handle spatial autocorrelation in cross-validation workflows with `spatial_train_test_split` and `SKCV` (spatial k-fold cross-validation)
 - Validation tools within [`dea-tools.validation`](https://knowledge.dea.ga.gov.au/notebooks/Tools/gen/dea_tools.validation/):
    * Compute common statistical metrics with `eval_metric`;
    * Generate random points over an `xarray` object for validation or training using `xr_random_sampling`.

![Example extraction of random samples from a classified `xarray.DataArray` using one of the sampling strategies available in the `xr_random_sampling` function.\label{fig:sampling}](figures/xr_random_sampling.png)

## Plotting 

The [`dea-tools.plotting`](https://knowledge.dea.ga.gov.au/notebooks/Tools/gen/dea_tools.plotting/) library has extensive functionality for generating beautiful imagery from `xarray` objects:

- Generate highly customisable animations to visualise changes over time in `xarray` datasets using `xr_animation`;
- Create true and false colour composite images from satellite data using `rgb`.

![True and false colour composites generated with the `dea-tools.plotting.rgb` function, using DEA GeoMAD composite images from 2024. Location: Norman River, Queensland.\label{fig:rgb}](figures/RGB_images.png)

# Research projects

`dea-tools` and the broader `dea-notebooks` repository support a wide range of scientific applications. These include but are not limited to agriculture and land cover mapping, wetland, coastal, and surface water monitoring, and climate and fire analysis. The `dea-notebooks` repository has already underpinned more than 25 peer-reviewed studies, demonstrating its robustness and adaptability across domains. Usage of the library is tracked [here](https://github.com/GeoscienceAustralia/dea-notebooks/blob/stable/USAGE.rst), providing transparency and insight into its adoption across research projects.

# References
