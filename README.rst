dea-notebooks
=============
Repository for Digital Earth Australia Jupyter Notebooks

Getting Started
===============

The basic structure of this repository is designed to keep 'all' of the DEA Jupyter Notebooks
in one place. The repository uses branches to manage individuals' notebooks, and to allow easy publishing
of notebooks ready to be shared.

To get started, clone this repository to a suitable location. This will most likely be a location you can 
access on the VDI, so you can easily work with your notebooks. Note that this repo is likely to become quite large,
so make sure you have enough space in the location you clone the repository to (i.e. probably not your home directory, 
but your directory on /g/data should be perfect). 

To clone the repo (assumes you are on the VDI):
* Navigate to the location you want the repository to sit using a Terminal window
* Type `git clone git@github.com:GeoscienceAustralia/dea-notebooks.git`
* A new folder called `dea-notebooks` will be created, which is a copy of the code repo
* `cd dea-notebooks`
* Use the command `git status` (at any time) to check which branch you are on and any changes you have made.
You should see that you are automatically on the `master` branch. This is the published branched of the repository. 
* To create your own branch, type `git checkout -b <yourname>` (where <yourname> will be the name of the new branch.
* You will automatically be changed to your new branch (you can use `git status` to check this). Any changes you make here will
not affect the other branches of the repository. 


Pushing back to the main repository
===================================
* To let the main repository know that you have created a new branch, you need to push it back up to the remote repository.
