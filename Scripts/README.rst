Scripts
=======

This folder originally contained Python functions and algorithms developed to assist in analysing DEA data (e.g. loading data, plotting, spatial analysis, machine learning). These have since been moved to ../Tools/ and incorporated into the `dea-tools` Python module. The files prefixed with `dea_` now import from dea-tools directly for compatibility with existing notebook code. New code should use dea-tools instead of the `dea_*` scripts in this folder.

Scripts beginning with `notebookapp_` are for use with their respective notebooks.

.. toctree::
   :maxdepth: 1
   :caption: Scripts
   
   dea_bandindices.py
   dea_bom.py
   dea_classificationtools.py
   dea_climate.py
   dea_coastaltools.py
   dea_dask.py
   dea_datahandling.py
   dea_plotting.py
   dea_spatialtools.py
   dea_temporal.py
   notebookapp_changefilmstrips.py
   notebookapp_crophealth.py
   notebookapp_miningrehab.py
