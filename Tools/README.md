# DEA Tools Python package

`dea_tools` is an open-source Python package providing functions and algorithms for geospatial analysis using Open Data Cube, Xarray, and Digital Earth Australia.
It includes utilities for loading data, plotting, spatial and temporal analysis, and applying machine learning to satellite data.

The package is organised into the following modules:

* `dea_tools.datahandling`: Tools for loading and managing DEA data (e.g. combining products, handling CRSs, pansharpening)
* `dea_tools.plotting`: Plotting tools for DEA data (e.g. RGB composites, animations, interactive maps)
* `dea_tools.bandindices`: Functions to calculate remote sensing indices (e.g. NDVI, NDWI)
* `dea_tools.spatial`: Spatial analysis utilities (e.g. rasterisation, vectorisation, contours, image processing)
* `dea_tools.temporal`: Tools for temporal analysis (e.g. phenology, time-series statistics, multi-dimensional regression)
* `dea_tools.classification`: Machine learning utilities (e.g. training and applying models on satellite data)
* `dea_tools.dask`: Utilities for parallel processing with Dask (e.g. creating scalable Dask clusters)
* `dea_tools.landcover`: Tools for accessing and visualising DEA Land Cover data
* `dea_tools.coastal`: Coastal and intertidal analysis tools (e.g. coastal change time series, sunglint mapping)
* `dea_tools.bom`: Accessing Bureau of Meteorology water data (e.g. gauge and discharge data)
* `dea_tools.waterbodies`: Accessing and analysing DEA Waterbodies data (e.g. loading waterbody time series)
* `dea_tools.maps`: Tools for interactive mapping (e.g. folium and ipyleaflet maps)
* `dea_tools.validation`: Tools for generating validation statistics (e.g. RMSE, R2, correlations)

## API documentation

A rendered version of the `dea-tools` API is available on the DEA Knowledge Hub (https://knowledge.dea.ga.gov.au/notebooks/Tools/).

## Installation

You can install `dea-tools` from PyPI with `pip` (https://pypi.org/project/dea-tools/).
By default `dea-tools` will be installed with [minimal dependencies](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/pyproject.toml), which excludes `datacube` and other difficult to install packages.

```console
pip install dea-tools
```

To install with `datacube` dependencies:
```console
pip install dea-tools[datacube]
```

To install with additonal STAC-loading dependencies:
```console
pip install dea-tools[stac]
```

To install with additonal Jupyter-related dependencies:
```console
pip install dea-tools[jupyter]
```

To install with other packages used in DEA Notebooks examples:
```console
pip install dea-tools[jupyter,dask_gateway,hdstats,notebooks]
```

You can also install `dea-tools` with *all* optional dependencies. **Note:** some of these dependencies are difficult to install. If you encounter issues, you may need to try the [Conda](#with-conda) instructions below.
```console
pip install dea-tools[all]
```

### With conda

If you encounter issues with the installation, try installing the package in a `conda` Python environment where [GDAL](https://pypi.org/project/GDAL/) and [pyproj](https://pypi.org/project/pyproj/) are already installed:

```console
wget -O conda-environment.yml https://raw.githubusercontent.com/opendatacube/datacube-core/develop/conda-environment.yml

mamba env create -f conda-environment.yml
conda activate cubeenv

pip install dea-tools
```

### Working on DEA Sandbox or NCI

To work with this module on the DEA Sandbox or National Computational Infrastructure environments without installing it, you can add the `Tools` directory to the system path from within your `dea-notebooks` directory:

```python
import sys
sys.path.insert(1, "../Tools/")
import dea_tools.datahandling  # or some other submodule
```

Alternatively, you can also do a local installation of `dea-tools`. To do this on the DEA Sandbox, run `pip` from the terminal from within your `dea-notebooks` directory:

```bash
pip install -e .
```

## Importing functions in Python

One `dea-tools` is installed, you can import functions using:

```python
from dea_tools.datahandling import load_ard
from dea_tools.plotting import rgb
```

## Citing DEA Tools

If you use any of the notebooks, code or tools in this repository in your work, please reference them using the following citation:

> Krause, C., Dunn, B., Bishop-Taylor, R., Adams, C., Burton, C., Alger, M., Chua, S., Phillips, C., Newey, V., Kouzoubov, K., Leith, A., Ayers, D., Hicks, A., DEA Notebooks contributors 2021. Digital Earth Australia notebooks and tools repository. Geoscience Australia, Canberra. https://doi.org/10.26186/145234
