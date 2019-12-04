.. Notebook Gallery Instructions:

Overview of DEA Notebooks
=========================
This documentation is designed to step the user through getting started with Digital Earth Australia (DEA), through to more complicated algorithms and workflows. If you need to join the NCI first, read about joining the NCI here:  https://docs.dea.ga.gov.au/connect/account.html.

Note that these functions have been developed by DEA users, not the DEA development team, and so are provided without warranty. If you find an error or bug in the functions, please either create an Issue in the Github repository, or fix it yourself and create a Pull request to contribute the updated function back into the repository (See the repository README for instructions on creating a Pull request).

The intended order of these notebook folders are:

1. `Beginners_guide <https://github.com/GeoscienceAustralia/dea-notebooks/tree/develop/Beginners_guide>`_

2. `DEA_datasets <https://github.com/GeoscienceAustralia/dea-notebooks/tree/develop/DEA_datasets>`_

3. `Frequently_used_code <https://github.com/GeoscienceAustralia/dea-notebooks/tree/develop/Frequently_used_code>`_

4. `Real_world_examples <https://github.com/GeoscienceAustralia/dea-notebooks/tree/develop/Real_world_examples>`_

The supporting scripts and data for the notebooks are kept in the following folders:

- `Scripts <https://github.com/GeoscienceAustralia/dea-notebooks/tree/develop/Scripts>`_

- `Supplementary_data <https://github.com/GeoscienceAustralia/dea-notebooks/tree/develop/Supplementary_data>`_

The *read-the-docs* version of this repository can be found at: `<https://docs.dea.ga.gov.au/>`_

If you are searching for a specific functionality, use the `Tags Index <https://docs.dea.ga.gov.au/genindex.html>`_ to search for a suitable example. If there is a functionality that has not been documented that you think should be, please create an `Issue` in the `dea-notebooks repository. <https://github.com/GeoscienceAustralia/dea-notebooks/issues>`_

The basic structure of this repository is designed to keep 'all' of the DEA Jupyter notebooks in one place. The repository uses branches to manage individuals' notebooks, and to allow easy publishing of notebooks ready to be shared. There are two main types of branches:

* `Master branch <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master>`_: where notebooks are put that are ready to be shared. Notebooks added to this branch will be published on the `DEA User Guide page <https://docs.dea.ga.gov.au/>`_. The master branch is protected, and requires changes to be approved via a ``pull request`` before changes are made to the branch. This is simply to avoid mistakes when pushing to this branch, and to allow a quick check of code before publishing.

* `Working branches <https://github.com/GeoscienceAustralia/dea-notebooks/branches>`_: these are typically named using the owner's name as the branch name (e.g. ``ClaireK``, ``BexDunn``). These are the working spaces for people and essentially your own place to play around with. The notebooks here do not need to be pretty or even finished. It's just a place to keep everything together. It also means that if you want to collaborate on a working version of a notebook, you can easily find and share notebooks.
