.. Notebook Gallery Instructions:

.. image:: Supplementary_data/dea_logo_wide.jpg
  :width: 900
  :alt: Digital Earth Australia logo

DEA Notebooks
#############

This is the notebooks and tools repository of Digital Earth Australia (DEA).

.. image:: https://img.shields.io/badge/DOI-10.26186/145234-0e7fbf.svg
  :target: https://doi.org/10.26186/145234
  :alt: DOI
.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
  :target: https://opensource.org/licenses/Apache-2.0
  :alt: Apache license
.. image:: https://img.shields.io/pypi/v/dea-tools
  :target: https://pypi.org/project/dea-tools/
  :alt: PyPI
.. image:: https://github.com/GeoscienceAustralia/dea-notebooks/actions/workflows/test_notebooks.yml/badge.svg?branch=develop
  :target: https://github.com/GeoscienceAustralia/dea-notebooks/actions/workflows/test_notebooks.yml
  :alt: Notebook testing

**Contribute:** We'd love your contribution! DEA Notebooks is an open-source project and welcomes contributions from everyone.

**License:** The code in this repository is licensed under the `Apache License, Version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>`_. DEA data is licensed under the `Creative Commons by Attribution 4.0 license <https://creativecommons.org/licenses/by/4.0/>`_.

**Documentation:** See the `DEA Notebooks Wiki <https://github.com/GeoscienceAustralia/dea-notebooks/wiki>`_.

**Contact:** For assistance with any of these notebooks and tools, please ask a question on our `Open Data Cube Slack channel <http://slack.opendatacube.org/>`_ or on the `GIS Stack Exchange <https://gis.stackexchange.com/questions/tagged/open-data-cube>`_ using the ``open-data-cube`` tag. You can also `report an issue on this repository <https://github.com/GeoscienceAustralia/dea-notebooks/issues>`_.

**Citation:** If you use this repository in your work, please reference it with the following citation.

    Krause, C., Dunn, B., Bishop-Taylor, R., Adams, C., Burton, C., Alger, M., Chua, S., Phillips, C., Newey, V., Kouzoubov, K., Leith, A., Ayers, D., Hicks, A., DEA Notebooks contributors 2021. Digital Earth Australia notebooks and tools repository. Geoscience Australia, Canberra. https://doi.org/10.26186/145234

We would also appreciate it if you add a citation of your work to our `USAGE <https://github.com/GeoscienceAustralia/dea-notebooks/blob/stable/USAGE.rst>`_ page.

----------

Introduction
============

This repository hosts Jupyter Notebooks, Python scripts and workflows for analysing `Digital Earth Australia (DEA) <https://www.ga.gov.au/dea>`_ satellite data and derived products. This documentation is designed to provide a guide to getting started with DEA, and to showcase the wide range of geospatial analyses that can be achieved using DEA data and open-source software including `Open Data Cube <https://www.opendatacube.org/>`_ and `xarray <http://xarray.pydata.org/en/stable/>`_.

The repository is based around the following directory structure (from simple to increasingly complex applications):

1. `Beginners_guide <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Beginners_guide>`_: *Introductory notebooks aimed at introducing Jupyter Notebooks and how to load, plot and interact with DEA data*

2. `DEA_products <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/DEA_products>`_: *Notebooks introducing DEA's satellite datasets and derived products, including how to load each dataset and any special features of the data*

3. `Interactive_apps <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Interactive_apps>`_: *Interactive apps and widgets that require little or no coding to run*

4. `How_to_guides <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/How_to_guides>`_: *A recipe book of simple code examples demonstrating how to perform common geospatial analysis tasks using DEA and open-source software*

5. `Real_world_examples <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Real_world_examples>`_: *More complex case study workflows demonstrating how DEA can be used to address real-world problems*

Supporting functions and data for the notebooks are kept in the following directories:

- `Tools <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Tools>`_: *Python module dea-tools, containing functions and algorithms developed to assist in analysing DEA data (e.g. loading data, plotting, spatial analysis, machine learning)* 

- `Supplementary_data <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Supplementary_data>`_: *Supplementary files required for the analyses above (e.g. images, rasters, shapefiles, training data)*

All notebooks in the ``dea-notebooks`` repository contain tags describing their functionality. If there is a functionality that has not been documented that you think should be, please create an 'Issue' in the `dea-notebooks repository. <https://github.com/GeoscienceAustralia/dea-notebooks/issues>`_

.. If you are searching for a specific functionality, use the `Tags Index </genindex/>`_ to search for a suitable example.

We encourage you to check out the other usages of our notebooks, code and tools at our `USAGE <https://github.com/GeoscienceAustralia/dea-notebooks/blob/stable/USAGE.rst>`_ page.

Contributing to DEA Notebooks
=============================

To get started, see these articles in the wiki.

* `Git workflow <https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Git-workflow>_`
* `Create a DEA Notebook <https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Create-a-DEA-Notebook>`_
* `Edit a DEA Notebook <https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Edit-a-DEA-Notebook>`_
