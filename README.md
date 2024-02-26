<img src="Supplementary_data/dea_logo_wide.jpg" width="900" alt="Digital Earth Australia logo" />

# DEA Notebooks

[![DOI](https://img.shields.io/badge/DOI-10.26186/145234-0e7fbf.svg)](https://doi.org/10.26186/145234) [![Apache license](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![PyPI](https://img.shields.io/pypi/v/dea-tools)](https://pypi.org/project/dea-tools/) [![Notebook testing](https://github.com/GeoscienceAustralia/dea-notebooks/actions/workflows/test_notebooks.yml/badge.svg?branch=develop)](https://github.com/GeoscienceAustralia/dea-notebooks/actions/workflows/test_notebooks.yml)

<br />

This is the DEA Notebooks and DEA Tools repository of [Digital Earth Australia](https://www.dea.ga.gov.au/).
You can view and interactive with these Notebooks on the
[DEA Sandbox](https://app.sandbox.dea.ga.gov.au/) and the
[DEA Knowledge Hub](https://docs.dea.ga.gov.au/).

**Contribute** &mdash; DEA Notebooks is open-source and we would love your contribution!
Learn [how to contribute](#contribute) below.

**License** &mdash; The code in this repository is licensed under the [Apache
License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). DEA
data is licensed under the [Creative Commons by Attribution 4.0
license](https://creativecommons.org/licenses/by/4.0/).

**Documentation** &mdash; See the [DEA Notebooks
Wiki](https://github.com/GeoscienceAustralia/dea-notebooks/wiki).

**Contact** &mdash; For assistance with any of these notebooks and tools,
please ask a question on our [Open Data Cube Slack
channel](http://slack.opendatacube.org/) or on the [GIS Stack
Exchange](https://gis.stackexchange.com/questions/tagged/open-data-cube)
using the `open-data-cube` tag. You can also [report an issue on this
repository](https://github.com/GeoscienceAustralia/dea-notebooks/issues).

**Citation** &mdash; If you use this repository in your work, please reference
it with the following citation.

> Krause, C., Dunn, B., Bishop-Taylor, R., Adams, C., Burton, C., Alger,
> M., Chua, S., Phillips, C., Newey, V., Kouzoubov, K., Leith, A.,
> Ayers, D., Hicks, A., DEA Notebooks contributors 2021. Digital Earth
> Australia notebooks and tools repository. Geoscience Australia,
> Canberra. <https://doi.org/10.26186/145234>

We would also appreciate it if you add your own citation to our
[USAGE](https://github.com/GeoscienceAustralia/dea-notebooks/blob/stable/USAGE.rst)
page.

## Introduction

This repository contains Jupyter Notebooks and Python tools for
for analysing Digital Earth Australia (DEA)
satellite data products. The notebooks are designed to demonstrate
how to use DEA tools and data to conduct a broad range of geospatial
analyses. They also demonstrate how to integrate with other open-source
software such as [Open Data Cube](https://www.opendatacube.org/) and
[xarray](http://xarray.pydata.org/en/stable/).





The repository is based around the following directory structure (from
simple to increasingly complex applications):

1. [Beginners_guide](https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Beginners_guide) &mdash;
   *Introductory notebooks aimed at introducing Jupyter Notebooks and
   how to load, plot and interact with DEA data*
1. [DEA_products](https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/DEA_products) &mdash;
   *Notebooks introducing DEA\'s satellite datasets and derived
   products, including how to load each dataset and any special
   features of the data*
1. [Interactive_apps](https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Interactive_apps) &mdash;
   *Interactive apps and widgets that require little or no coding to
   run*
1. [How_to_guides](https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/How_to_guides) &mdash;
   *A recipe book of simple code examples demonstrating how to perform
   common geospatial analysis tasks using DEA and open-source software*
1. [Real_world_examples](https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Real_world_examples) &mdash;
   *More complex case study workflows demonstrating how DEA can be used
   to address real-world problems*

Supporting functions and data for the notebooks are kept in the
following directories:

-   [Tools](https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Tools):
    *Python module dea-tools, containing functions and algorithms
    developed to assist in analysing DEA data (e.g. loading data,
    plotting, spatial analysis, machine learning)*
-   [Supplementary_data](https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Supplementary_data):
    *Supplementary files required for the analyses above (e.g. images,
    rasters, shapefiles, training data)*

All notebooks in the `dea-notebooks` repository contain tags describing
their functionality. If there is a functionality that has not been
documented that you think should be, please create an \'Issue\' in the
[dea-notebooks
repository.](https://github.com/GeoscienceAustralia/dea-notebooks/issues)

We encourage you to check out the other usages of our notebooks, code
and tools at our
[USAGE](https://github.com/GeoscienceAustralia/dea-notebooks/blob/stable/USAGE.rst)
page

<span id="contribute"></span>

## How to contribute

To get started, see these articles in the wiki.

* [Git workflow](https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Git-workflow)
* [Create a DEA Notebook](https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Create-a-DEA-Notebook)
* [Edit a DEA Notebook](https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Edit-a-DEA-Notebook)

