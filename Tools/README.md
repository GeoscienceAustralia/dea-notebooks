<img src="https://raw.githubusercontent.com/GeoscienceAustralia/dea-notebooks/stable/Supplementary_data/dea_logo_wide.jpg" width="900" alt="Digital Earth Australia logo" />

# DEA Tools Python package

[![DOI](https://img.shields.io/badge/DOI-10.26186/145234-0e7fbf.svg)](https://doi.org/10.26186/145234) [![Apache license](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![Discord](https://img.shields.io/discord/1212501566326571070?label=Discord&logo=discord&logoColor=white&color=7289DA)](https://discord.com/invite/4hhBQVas5U)

`dea-tools` is an open-source Python package for geospatial analysis of satellite data using Digital Earth Australia, Open Data Cube, and Xarray.
It provides a broad set of utilities for loading, visualising, transforming, and analysing Earth Observation (EO) data across space and time.

The package includes tools for:

* 📦 **Data handling**: Load and combine DEA data products, manage projections and resolutions.
* 🗺️ **Visualisation**: Create static and interactive maps, RGB plots, and animations.
* 🛰️ **Remote sensing indices**: Calculate band indices such as NDVI, NDWI, and more.
* 🌐 **Spatial and temporal analysis**: Apply raster/vector operations, extract contours, compute temporal stats, and model change over time.
* 🤖 **Machine learning and segmentation**: Train and apply classifiers, or run image segmentation workflows.
* ⚙️ **Parallel processing**: Set up Dask clusters for scalable processing of large datasets.
* 🌏 **Domain-specific tools**: Analyse coastal change, intertidal zones, land cover, wetland and waterbody dynamics, and climate datasets.

## API documentation

Full API documentation describing the modules and functions available in `dea-tools` is available on the [DEA Knowledge Hub](https://knowledge.dea.ga.gov.au/notebooks/Tools/).

## Installation

You can install `dea-tools` from PyPI with `pip` (https://pypi.org/project/dea-tools/).

By default `dea-tools` will be installed with [minimal dependencies](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/pyproject.toml), which excludes `datacube` and other difficult to install packages:

```console
pip install dea-tools
```

To install with `datacube` dependencies (note that this requires access to a datacube database):
```console
pip install dea-tools[datacube]
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
from dea_tools.datahandling import load_ard  # or some other function
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
