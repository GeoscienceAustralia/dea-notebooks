.. Notebook Gallery Instructions:

Digital Earth Australia Notebooks
#################################

**License:** The code in this repository is licensed under the `Apache License, Version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>`_. Digital Earth Australia data is licensed under the `Creative Commons by Attribution 4.0 license <https://creativecommons.org/licenses/by/4.0/>`_.

**Contact:** If you need assistance with any of the Jupyter Notebooks or Python code in this repository, please post a question on the `Open Data Cube Slack channel <http://slack.opendatacube.org/>`_ or on the `GIS Stack Exchange <https://gis.stackexchange.com/questions/ask?tags=open-data-cube>`_ using the ```open-data-cube``` tag (you can view `previously asked questions here <https://gis.stackexchange.com/questions/tagged/open-data-cube>`_). If you would like to report an issue with this notebook, you can `file one on Github <https://github.com/GeoscienceAustralia/dea-notebooks>`_.

----------

The Digital Earth Australia Notebooks repository (``dea-notebooks``) hosts Jupyter Notebooks, Python scripts and workflows for analysing Digital Earth Australia (DEA) satellite data and derived products. This documentation is designed to provide a guide to getting started with DEA, and to showcase the wide range of geospatial analyses that can be achieved using DEA data and open-source software including ``Open Data Cube`` and ``xarray``.

The repository is based around the following directory structure (from simple to increasingly complex applications):

1. `Beginners_guide <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Beginners_guide>`_: *Introductory notebooks aimed at introducing Jupyter Notebooks and how to load, plot and interact with DEA data*

2. `DEA_datasets <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/DEA_datasets>`_: *Notebooks introducing DEA's satellite datasets and derived products, including how to load each dataset and any special features of the data*

3. `Frequently_used_code <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Frequently_used_code>`_: *A recipe book of simple code examples demonstrating how to perform common geospatial analysis tasks using DEA and open-source software*

4. `Real_world_examples <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Real_world_examples>`_: *More complex workflows demonstrating how DEA can be used to address real-world problems*

The supporting scripts and data for the notebooks are kept in the following directories:

- `Scripts <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Scripts>`_: *Python functions and algorithms for developed to assist in analysing DEA data (e.g. loading data, plotting, spatial analysis, machine learning)* 

- `Supplementary_data <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Supplementary_data>`_: *Supplementary files required for the analyses above (e.g. images, rasters, shapefiles, training data)*

The Jupyter notebooks on the ``master`` branch of this repository are used to generate the **Digital Earth Australia User Guide** located at: `<https://docs.dea.ga.gov.au/>`_

All notebooks in the dea-notebooks repository contain tags describing their functionality. If you are searching for a specific functionality, use the `Tags Index <https://docs.dea.ga.gov.au/genindex.html>`_ to search for a suitable example. If there is a functionality that has not been documented that you think should be, please create an 'Issue' in the `dea-notebooks repository. <https://github.com/GeoscienceAustralia/dea-notebooks/issues>`_


Contributing to DEA Notebooks
=============================

DEA Notebooks template notebook
-------------------------------
An empty template notebook has been developed to ensure that Jupyter notebooks in the ``dea-notebooks`` repository are consistent and well-documented so they can be understood by future users, and rendered correctly in the `DEA User Guide <https://docs.dea.ga.gov.au/>`_.

The template notebook contains useful general advice on writing and formatting Jupyter notebooks. The template can be found here: `DEA_notebooks_template.ipynb <https://github.com/GeoscienceAustralia/dea-notebooks/blob/master/DEA_notebooks_template.ipynb>`_

Master and working branches
---------------------------

The ``dea-notebooks`` repository uses 'branches' to manage individuals' notebooks, and to allow easy publishing of notebooks ready to be shared. There are two main types of branches:

* `Master branch <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master>`_: The ``master`` branch is where notebooks are put that are ready to be shared publicly. Notebooks added to this branch will become part of the offical DEA documentation and are published on the `DEA User Guide <https://docs.dea.ga.gov.au/>`_. The ``master`` branch is protected, and requires changes to be approved via a ``pull request`` before they appear on the branch. 

* `Working branches <https://github.com/GeoscienceAustralia/dea-notebooks/branches>`_: All other branches in the repository are working spaces for users of ``dea-notebooks``. They have a unique name (typically named after the user, e.g. ``ClaireK``, ``BexDunn``). The notebooks on these branches can be works-in-progress and do not need to be pretty or complete. By using a working branch, it is easy to use scripts and algorithms from ``dea-notebooks`` in your own work, or share and collaborate on a working version of a notebook or code.

Getting started with DEA notebooks
----------------------------------

There are two main options for interacting with ``dea-notebooks``:

- DEA notebooks using git: Git is a version-control software designed to help track changes to files and collaborate with multiple users on a project. Using ``git`` is the recommended workflow for working with ``dea-notebooks`` as it makes it easy to stay up to date with the latest versions of functions and code, and makes it impossible to lose your work. 
 - Refer to the repository's `Guide to DEA Notebooks using Git <https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Guide-to-using-Git-on-the-DEA-Sandbox>`_ wiki article.

- DEA notebooks using Github: Alternatively, the Github website can be used to upload and modify the ``dea-notebooks`` repository directly. This can be a good way to get started with ``dea-notebooks``. 
 - Refer to the repository's `Guide to DEA Notebooks using the Github website <https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Guide-to-using-Git-on-the-DEA-Sandbox>`_ wiki article.
