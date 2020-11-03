.. Notebook Gallery Instructions:

.. image:: Supplementary_data/dea_logo_wide.jpg
  :width: 900
  :alt: Digital Earth Australia logo

Digital Earth Australia Notebooks
#################################

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
  :target: https://opensource.org/licenses/Apache-2.0
  :alt: Digital Earth Australia logo

**License:** The code in this repository is licensed under the `Apache License, Version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>`_. Digital Earth Australia data is licensed under the `Creative Commons by Attribution 4.0 license <https://creativecommons.org/licenses/by/4.0/>`_.

**Contact:** If you need assistance with any of the Jupyter Notebooks or Python code in this repository, please post a question on the `Open Data Cube Slack channel <http://slack.opendatacube.org/>`_ or on the `GIS Stack Exchange <https://gis.stackexchange.com/questions/ask?tags=open-data-cube>`_ using the ``open-data-cube`` tag (you can view `previously asked questions here <https://gis.stackexchange.com/questions/tagged/open-data-cube>`_). If you would like to report an issue with this notebook, you can `file one on Github <https://github.com/GeoscienceAustralia/dea-notebooks>`_.

----------

The Digital Earth Australia Notebooks repository (``dea-notebooks``) hosts Jupyter Notebooks, Python scripts and workflows for analysing `Digital Earth Australia (DEA) <https://www.ga.gov.au/dea>`_ satellite data and derived products. This documentation is designed to provide a guide to getting started with DEA, and to showcase the wide range of geospatial analyses that can be achieved using DEA data and open-source software including `Open Data Cube <https://www.opendatacube.org/>`_ and `xarray <http://xarray.pydata.org/en/stable/>`_.

The repository is based around the following directory structure (from simple to increasingly complex applications):

1. `Beginners_guide <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Beginners_guide>`_: *Introductory notebooks aimed at introducing Jupyter Notebooks and how to load, plot and interact with DEA data*

2. `DEA_datasets <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/DEA_datasets>`_: *Notebooks introducing DEA's satellite datasets and derived products, including how to load each dataset and any special features of the data*

3. `Frequently_used_code <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Frequently_used_code>`_: *A recipe book of simple code examples demonstrating how to perform common geospatial analysis tasks using DEA and open-source software*

4. `Real_world_examples <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Real_world_examples>`_: *More complex workflows demonstrating how DEA can be used to address real-world problems*

5. `Scientific_workflows <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Scientific_workflows>`_: *Production code and notebooks for generating published DEA products or analysis tools*

The supporting scripts and data for the notebooks are kept in the following directories:

- `Scripts <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Scripts>`_: *Python functions and algorithms for developed to assist in analysing DEA data (e.g. loading data, plotting, spatial analysis, machine learning)* 

- `Supplementary_data <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable/Supplementary_data>`_: *Supplementary files required for the analyses above (e.g. images, rasters, shapefiles, training data)*

The Jupyter notebooks on the ``stable`` branch of this repository are used to generate the **Digital Earth Australia User Guide** located at: `<https://docs.dea.ga.gov.au/>`_

All notebooks in the dea-notebooks repository contain tags describing their functionality. If you are searching for a specific functionality, use the `Tags Index <https://docs.dea.ga.gov.au/genindex.html>`_ to search for a suitable example. If there is a functionality that has not been documented that you think should be, please create an 'Issue' in the `dea-notebooks repository. <https://github.com/GeoscienceAustralia/dea-notebooks/issues>`_

----------

Getting started with DEA Notebooks
==================================

To get started with using ``dea-notebooks``, `visit the DEA Notebooks Wiki page <https://github.com/GeoscienceAustralia/dea-notebooks/wiki>`_. This page includes guides for getting started on both the `DEA Sandbox <https://github.com/GeoscienceAustralia/dea-notebooks/wiki#getting-started-on-the-dea-sandbox>`_ and `NCI environments <https://github.com/GeoscienceAustralia/dea-notebooks/wiki#getting-started-on-the-nci>`_.

Once you're set up, there are two main options for interacting with ``dea-notebooks`` and contributing back to the repository:

* **DEA notebooks using git**: Git is a version-control software designed to help track changes to files and collaborate with multiple users on a project. Using ``git`` is the recommended workflow for working with ``dea-notebooks`` as it makes it easy to stay up to date with the latest versions of functions and code and makes it impossible to lose your work. 

  * Refer to the repository's `Guide to using DEA Notebooks with git <https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Guide-to-using-DEA-Notebooks-with-git>`_ wiki article.

* **DEA notebooks using Github**: Alternatively, the Github website can be used to upload and modify the ``dea-notebooks`` repository directly. This can be a good way to get started with ``dea-notebooks``. 

  * Refer to the repository's `Guide to DEA Notebooks using the Github website <https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Guide-to-using-DEA-Notebooks-with-the-Github-website>`_ wiki article.

----------

Contributing to DEA Notebooks
=============================

Develop, stable and working branches
------------------------------------

The ``dea-notebooks`` repository uses 'branches' to manage individuals' notebooks, and to allow easy publishing of notebooks ready to be shared. There are two main types of branches:

* `develop branch <https://github.com/GeoscienceAustralia/dea-notebooks/tree/develop>`_: The ``develop`` branch is the **default branch** where notebooks are put as they are being prepared to be shared publicly. Notebooks added to this branch will be periodically merged into the ``stable`` branch after testing and evaluation. The ``develop`` branch is protected and requires changes to be approved via a 'pull request' and review checklist before they appear on the branch.
* `stable branch <https://github.com/GeoscienceAustralia/dea-notebooks/tree/stable>`_: The ``stable`` branch contains DEA's collection of publicly available notebooks. Notebooks added to this branch will become part of the official DEA documentation and are published on the `DEA User Guide <https://docs.dea.ga.gov.au/>`_. The ``stable`` branch is protected, and is periodically updated with new content from the ``develop`` branch via a 'pull request' (for ``develop`` > ``stable`` pull requests, *merge using the 'Create a merge commit' option*).
* `Working branches <https://github.com/GeoscienceAustralia/dea-notebooks/branches>`_: All other branches in the repository are working spaces for users of ``dea-notebooks``. They have a unique name (typically named after the user, e.g. ``ClaireK``, ``BexDunn``). The notebooks on these branches can be works-in-progress and do not need to be pretty or complete. By using a working branch, it is easy to use scripts and algorithms from ``dea-notebooks`` in your own work or share and collaborate on a working version of a notebook or code.

 
Publishing notebooks to the stable branch
-----------------------------------------

Once you have a notebook that is ready to be published on the ``develop`` branch, you can submit a 'pull request' in the `Pull requests tab at the top of the repository <https://github.com/GeoscienceAustralia/dea-notebooks/pulls>`_. The default pull request template contains a check-list to ensure that all ``stable`` branch Jupyter notebooks are consistent and well-documented so they can be understood by future users, and rendered correctly in the `DEA User Guide <https://docs.dea.ga.gov.au/>`_. Please ensure that as many of these checklist items are complete as possible or leave a comment in the pull request asking for help with any remaining checklist items.

Draft pull requests
^^^^^^^^^^^^^^^^^^^

For pull requests you would like help with or that are a work in progress, consider using Github's `draft pull request <https://github.blog/2019-02-14-introducing-draft-pull-requests/>`_ feature. This indicates that your work is still a draft, allowing you to get feedback from other DEA users before it is published on the ``develop` branch.

DEA Notebooks template notebook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A template notebook has been developed to make it easier to create new notebooks that meet all the pull request checklist requirements. The template notebook contains a simple structure and useful general advice on writing and formatting Jupyter notebooks. The template can be found here: `DEA_notebooks_template.ipynb <https://github.com/GeoscienceAustralia/dea-notebooks/blob/stable/DEA_notebooks_template.ipynb>`_

Using the template is not required for working branch notebooks but is *highly recommended* as it will make it much easier to publish any notebooks on ``develop`` in the future.

Approving pull requests
-----------------------

Anyone with admin access to the ``dea-notebooks`` repository can approve 'pull requests'. You can see a list of the 'pull requests' ready for review in the `Pull requests tab at the top of the repository <https://github.com/GeoscienceAustralia/dea-notebooks/pulls>`_. Click this tab, then click on the open pull request. You will need to review the code before you can approve the request. Ensure that all items in the pull request checklist have been ticked off and incorporated into the notebook. To make changes to someone else's pull request directly, first check out the branch you want to edit (e.g. ``pull_request_branch``):

.. code-block:: console

   git pull
   git checkout --track origin/pull_request_branch

Commit and push any changes you make, which will become part of the open pull request.

If the notebook meets all the checklist requirements, click the green 'Review' button and click 'Approve' (with an optional comment). You can also 'Request changes' here if any of the checklist items are not complete.

Once the pull request has been approved, you can merge it into the ``develop`` branch. Select the 'Squash and merge' option from the drop-down menu to the right of the green 'merge' button. Once you have merged the new branch in, you need to delete the branch. There is a button on the page that asks you if you would like to delete the now merged branch. Select 'Yes' to delete it.
