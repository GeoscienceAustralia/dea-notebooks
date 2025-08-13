DEA Tools Python package
========================

``dea_tools`` is an open-source Python package for geospatial analysis of satellite data using Digital Earth Australia, Open Data Cube, and Xarray.
It provides a broad set of utilities for loading, visualising, transforming, and analysing Earth Observation (EO) data across space and time.

This package is installed by default on the DEA Sandbox.
You can install it to your own environment from `PyPi <https://pypi.org/project/dea-tools/>`_ by running ``pip install dea-tools``. Learn more in the `DEA Tools Readme <https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/README_tools.md>`_.

Core modules
------------

.. autosummary::
   :toctree: gen

   dea_tools.datahandling
   dea_tools.plotting
   dea_tools.spatial
   dea_tools.temporal
   dea_tools.bandindices
   dea_tools.classification
   dea_tools.bom
   dea_tools.coastal
   dea_tools.dask
   dea_tools.landcover
   dea_tools.maps
   dea_tools.validation
   dea_tools.waterbodies
   dea_tools.wetlands
   
Apps and widgets
-----------------

``dea_tools`` interactive app sub-packages can be accessed through ``dea_tools.app``.

.. autosummary::
   :toctree: gen
   
   dea_tools.app.animations
   dea_tools.app.changefilmstrips
   dea_tools.app.crophealth
   dea_tools.app.deacoastlines
   dea_tools.app.geomedian
   dea_tools.app.imageexport
   dea_tools.app.miningrehab
   dea_tools.app.wetlandsinsighttool.py
   dea_tools.app.widgetconstructors

``dea_tools.mosaics`` is a sub-module for generating COG mosaics and VRTs that add colour schemes to them.

.. autosummary::
   :toctree: gen

    dea_tools.mosaics.cog
    dea_tools.mosaics.vrt

License
-------

The code in this module is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0).

Digital Earth Australia data is licensed under the Creative Commons by
Attribution 4.0 license (https://creativecommons.org/licenses/by/4.0/).

Contact
-------

If you need assistance, please post a question on the Open Data
Cube Discord chat (https://discord.com/invite/4hhBQVas5U) or on the GIS Stack
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube)
using the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, you can file one on
GitHub: https://github.com/GeoscienceAustralia/dea-notebooks/issues
