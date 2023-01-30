dea-tools
=========

Python functions and algorithms developed to assist in analysing Digital Earth Australia (DEA) data (e.g. loading data, plotting, spatial analysis, machine learning). This includes the following modules:

**Loading data**

-  ``dea_tools.datahandling``: Loading and handling DEA data (e.g. combining multiple products, handling CRSs, pansharpening)

**Plotting and transforming data**

-  ``dea_tools.plotting``: Plotting DEA data (e.g. RGB plots, animations, interactive maps)
-  ``dea_tools.bandindices.py``: Calculating remote sensing band indices (e.g. NDVI, NDWI)

**Spatial and temporal analysis**

-  ``dea_tools.spatial``: Spatial analysis tools (e.g. rasterising, vectorising, contour extraction, image processing)
-  ``dea_tools.temporal``: Temporal analysis tools (e.g. phenology, temporal statistics, multi-dimensional regression)

**Classification and segmentation**

-  ``dea_tools.classification.py``: Machine learning classification (e.g. training and applying machine learning models on satellite data)
-  ``dea_tools.segmentation.py``: Image segmentation tools (e.g. applying image segmentation with RSGISLIB)

**Parallel processing**

-  ``dea_tools.dask``: Parallel processing with Dask (e.g. creating Dask clusters for scalable analysis)

**Domain-specific analysis**

-  ``dea_tools.land_cover``: Functions for plotting Digital Earth Australia Land Cover data.
-  ``dea_tools.coastal``: Coastal and intertidal analysis tools (e.g. tidal tagging, coastal change timeseries)
-  ``dea_tools.bom``: Loading Bureau of Meteorology water data service data (e.g. gauge data, discharge data)
-  ``dea_tools.climate``: Retrieving and manipulating gridded climate data (e.g. ERA5)
-  ``dea_tools.waterbodies``: Loading and processing DEA Waterbodies data (e.g. finding and loading waterbody timeseries data)

Installation
------------

With conda
~~~~~~~~~~

.. code-block:: bash

    wget -O conda-environment.yml https://raw.githubusercontent.com/opendatacube/datacube-core/develop/conda-environment.yml

    mamba env create -f conda-environment.yml
    conda activate cubeenv


Install dea-tools
~~~~~~~~~~~~~~~~~

Install the package from the source on any system with ``pip``:

.. code-block:: bash

    pip install dea-tools

To work with this module on the DEA Sandbox or National Computational Infrastructure environments without installing it, you can add the ``Tools`` directory to the system path from within the ``dea-notebooks`` repository:

.. code-block:: python

   import sys
   sys.path.insert(1, '../Tools/')
   import dea_tools.datahandling  # or some other submodule

You can also ``pip install`` the module directly from the local ``Tools`` directory. To do this on the DEA Sandbox, run ``pip`` from the terminal:

.. code-block:: bash

   pip install -e Tools/


Importing functions in Python
-----------------------------

To use functions from ``dea-tools``, import them using:

.. code-block:: python

   from dea_tools.datahandling import load_ard
   from dea_tools.plotting import rgb


Citing DEA Tools
----------------

If you use any of the notebooks, code or tools in this repository in your work, please reference them using the following citation:

    Krause, C., Dunn, B., Bishop-Taylor, R., Adams, C., Burton, C., Alger, M., Chua, S., Phillips, C., Newey, V., Kouzoubov, K., Leith, A., Ayers, D., Hicks, A., DEA Notebooks contributors 2021. Digital Earth Australia notebooks and tools repository. Geoscience Australia, Canberra. https://doi.org/10.26186/145234


Building and Releasing
----------------------

This section is only relevant to you if you are a developer of this package.

Building and releasing dea-tools requires that the package is built in-place. Either build with an editable pip installation or with ``pip>=21.2`` and ``--use-feature=in-tree-build``. Building will generate a file, ``dea_tools/__version__.py``, that is dynamic on release. It should not be committed. ``setup.py`` will detect if ``__version__.py`` exists and change its behaviour accordingly.

Build instructions:

.. code-block:: bash

        cd Tools
        rm dea_tools/__version__.py  # if necessary
        pip install . --use-feature=in-tree-build
        python -m build
