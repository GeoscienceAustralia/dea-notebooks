dea-notebooks
=============
Repository for Digital Earth Australia Jupyter Notebooks.

The basic structure of this repository is designed to keep 'all' of the DEA Jupyter Notebooks
in one place. The repository uses branches to manage individuals' notebooks, and to allow easy publishing
of notebooks ready to be shared.

The structure of the repository is fairly simple:
* master branch - where notebooks are put that are ready to be shared. Notebooks added to this branch will be published
on the DEA documentation page in a notebook gallery.
* working branches - these are named using the owner's name as the branch name (e.g. ``ClaireK``, ``BexDunn``). These are the working
spaces for people and essentially your own place to play around with. The notebooks here do not need to be pretty or even finished. It's just
a place to keep everything together. It also means that if you want to collaborate on a working version of a notebook, you can easily
find and share notebooks.

**Note**: The master branch is protected, and will require a pull request for changes to be made to this branch. This is simply to avoid 
mistakes when pushing to this branch, and to allow a quick check of code before publishing. The check is basically just looking for 
the existence of required metadata, and that the file name has been added to the .rst index so it can be published on the DEA documentation website.

Getting Started
===============
To get started, clone this repository to a suitable location. This will most likely be a location you can 
access on the VDI, so you can easily work with your notebooks. Note that this repo is likely to become quite large,
so make sure you have enough space in the location you clone the repository to (i.e. probably not your home directory, 
but your directory on /g/data should be perfect). 

To clone the repo (assumes you are on the VDI):
-----------------------------------------------
* Navigate to the location you want the repository to sit using a Terminal window
* Type ``git clone git@github.com:GeoscienceAustralia/dea-notebooks.git``
* A new folder called ``dea-notebooks`` will be created, which is a copy of the code repo
* ``cd dea-notebooks``
* Use the command ``git status`` (at any time) to check which branch you are on and any changes you have made.
You should see that you are automatically on the ``master`` branch. This is the published branched of the repository. 
* To create your own branch, type ``git checkout -b <yourname>`` (where <yourname> will be the name of the new branch.
* You will automatically be changed to your new branch (you can use ``git status`` to check this). Any changes you make here will
not affect the other branches of the repository. 

Setting up your own version of the repo
=======================================
You will notice that your branch of the repo contains a copy of everything in the master branch. This probably isn't what you 
actually want. You can feel free to delete everything that is automatically put in your own branch, and start from scratch with 
your own directory structures. 

**Note**: Make sure you are on your own branch *before* deleting everything. You can check this with ``git status``. If you happen to delete
everything from the master branch, it can be restored (that's the wonder of version control), but try to avoid this in the first place.

To delete folders (or files) in a git managed repository, use ``git rm <file>``. This tells git you are deleting a file from the tracked
repository, which makes things a lot cleaner when you go to commit those changes later on. If you would like to delete a whole directory, 
you need to add the `-r` (recursive) flag to the command; ``git rm -r algorithms``. 

Committing and pushing your changes back to the main repository
===============================================================
The new branch you have created exists in your local version of the repository, but you wont yet see it on the git website because you 
haven't told it about your new branch yet. To do this, you will need to commit and then push your changes. If you now type ``git status``
you will see two groups of files; those git is tracking and has noticed have changed since the last commit, and those git is not tracking. 
To add the new files and folders you have created to the git tracked repo, type ``git add <file/folder>``. Go through all the folders you would
like git to track and ``git add`` them. Once you are ready to commit your changes, type ``git commit -m "this is a short description of 
the changes you have made"``. 

As there will be multiple people all working off the same repository, you should type ``git pull`` prior to pushing your commit. This will
make sure you have the latest version of the repository, and will hopefully avoid any potential merge conflicts when you go to push. 

Assuming the pull request didn't throw up any errors, you can now push your commit. To do this, type ``git push origin <your branch name>``. Git
will now connect to the remote repository and add your commit to the GitHub repo. You should now be able to see your new branch on the online
dea-notebooks repo.

Publishing finished notebooks
=============================
The master branch of dea-notebooks is where notebooks go that you are ready to share and publish. Note that even once the notebooks are published,
you can still edit and update them - this does not close them off to you for further work. 

To publish a notebook to the master branch, you will need to complete a 'push request'. 

Metadata requirements for publishing
------------------------------------
The notebook name should be descriptive and contain no spaces.

The ensure that the published notebooks are actually searchable and useable, the first cell of the notebook must have the following metadata
as a minumum:
* **What does this notebook do?** Include a fairly detailled description of what the notebook does. This will allow someone looking
for an example of a particular functionality to decide whether this notebook is likely to help them. 
* **Date** That the notebook was finalised. This is just to give an indication of the currency of the notebook, and when it was last working.
* **Author** Who wrote it?

You can of course provide additional information if you choose, e.g. background, purpose etc.

As an example...

# Getting started with Sentinel 2 data

**Background** As of mid-February 2018, Sentinel 2 data is available to access within the a development environment on AWS. There are a 
number of things that need to be done prior to gaining access to the Sentinel 2 archive. For the purpose of this notebook, we will assume 
you have successfully gained access to the AWS environment where Sentinel 2 data is currently housed. 

**What does this notebook do?** This notebook steps you through how to load in and plot up data from Sentinel 2. It explores the data that 
are available from the Sentinel 2 satellite, and briefly describes the Sentinel satellite bands. It then loads in the ``s2a_ard_granule`` 
product and plots it up in true and false colour. It uses the provided pixel quality data to filters the example scene based on ``clear`` 
pixels. 

**Date**: February 2018.

**Author**: Claire Krause

Tagging
-------
