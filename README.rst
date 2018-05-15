.. Notebook Gallery Instructions:

=====================
About this documentation
=====================
This documentation is designed to step the user through getting started with DEA, through to more complicated algorithms and workflows. 
The intended order of these notebook folders are:

1. Getting_started

2. DEA_datasets

3. Integrating_external_data

4. Index_calculation

5. Temporal_analysis

6. Composite_generation

7. Image_classification

8. Outputting_data

9. Workflows

10. Scripts

If you are searching for a specific functionality, use the :doc:`Tags Index </genindex>` to search for a suitable example. If there is a functionality that has not been documented that you think should be, please create an `Issue` in the `dea-notebooks repository<https://github.com/GeoscienceAustralia/dea-notebooks>`_. 

=============================
Notebook Gallery Instructions
=============================
Repository for Digital Earth Australia Jupyter Notebooks.

The basic structure of this repository is designed to keep 'all' of the DEA Jupyter Notebooks in one place. The repository uses branches to manage individuals' notebooks, and to allow easy publishing of notebooks ready to be shared.

The structure of the repository is fairly simple:

* master branch - where notebooks are put that are ready to be shared. Notebooks added to this branch will be published on the DEA documentation page in a notebook gallery.

* working branches - these are named using the owner's name as the branch name (e.g. ``ClaireK``, ``BexDunn``). These are the working spaces for people and essentially your own place to play around with. The notebooks here do not need to be pretty or even finished. It's just a place to keep everything together. It also means that if you want to collaborate on a working version of a notebook, you can easily find and share notebooks.

**Note**: The master branch is protected, and will require a pull request for changes to be made to this branch. This is simply to avoid mistakes when pushing to this branch, and to allow a quick check of code before publishing. The check is basically just looking for the existence of required metadata, and that the file name has been added to the .rst index so it can be published on the DEA documentation website.

Getting Started
===============
To get started, clone this repository to a suitable location. This will most likely be a location you can  access on the VDI, so you can easily work with your notebooks. Note that this repo is likely to become quite large, so make sure you have enough space in the location you clone the repository to (i.e. probably not your home directory, but your directory on /g/data should be perfect). 

To clone the repo (onto the VDI):
-----------------------------------------------
* Navigate to the location you want the repository to sit using a Terminal window
* Type ``git clone git@github.com:GeoscienceAustralia/dea-notebooks.git``
* A new folder called ``dea-notebooks`` will be created, which is a copy of the code repo
* ``cd dea-notebooks``
* Use the command ``git status`` (at any time) to check which branch you are on and any changes you have made. You should see that you are automatically on the ``master`` branch. This is the published branched of the repository. 
* To create your own branch, type ``git checkout -b <yourname>`` (where <yourname> will be the name of the new branch).
* You will automatically be changed to your new branch (you can use ``git status`` to check this). Any changes you make here will not affect the other branches of the repository. 

Setting up your own version of the repo
=======================================
You will notice that your branch of the repo contains a copy of everything in the master branch. This probably isn't what you actually want. You can feel free to delete everything that is automatically put in your own branch, and start from scratch with your own directory structures. 

**Note**: Make sure you are on your own branch *before* deleting everything. You can check this with ``git status``. If you happen to delete everything from the master branch, it can be restored (that's the wonder of version control), but try to avoid this in the first place.

To delete folders (or files) in a git managed repository, use ``git rm <file>``. This tells git you are deleting a file from the tracked repository, which makes things a lot cleaner when you go to commit those changes later on. If you would like to delete a whole directory, you need to add the `-r` (recursive) flag to the command; ``git rm -r algorithms``. 

Committing and pushing your changes back to the main repository
===============================================================
The new branch you have created exists in your local version of the repository, but you wont yet see it on the git website because you haven't told it about your new branch yet. To do this, you will need to commit and then push your changes. If you now type ``git status`` you will see two groups of files; those git is tracking and has noticed have changed since the last commit, and those git is not tracking. 
To add the new files and folders you have created to the git tracked repo, type ``git add <file/folder>``. Go through all the folders you would like git to track and ``git add`` them. Once you are ready to commit your changes, type ``git commit -m "this is a short description of the changes you have made"``. 

As there will be multiple people all working off the same repository, you should type ``git pull`` prior to pushing your commit. This will make sure you have the latest version of the repository, and will hopefully avoid any potential merge conflicts when you go to push. 

Assuming the pull request didn't throw up any errors, you can now push your commit. To do this, type ``git push -u origin <your branch name>``. Git will now connect to the remote repository and add your commit to the GitHub repo. You should now be able to see your new branch on the online dea-notebooks repo. The ``-u`` switch will set up your branch to properly track the remote branch of the same name. If you do a ``git pull`` and get a message that says ``you have not told me which branch to merge with``, this is because the local and remote repos were not set up to talk to each other properly. Easy fix! Type ``git branch --set-upstream <branch> origin/<branch>``. Git should now be happy.

Publishing finished notebooks
=============================
The master branch of dea-notebooks is where notebooks go that you are ready to share and publish. Note that even once the notebooks are published, you can still edit and update them - this does not close them off to you for further work. 

To publish a notebook to the master branch, you will need to complete a ``pull`` request (see below). 

Metadata requirements for publishing
------------------------------------
The notebook name should be descriptive and contain no spaces.

The ensure that the published notebooks are actually searchable and useable, the first cell of the notebook must have the following metadata
as a minumum:

* **What does this notebook do?** Include a fairly detailled description of what the notebook does. This will allow someone looking for an example of a particular functionality to decide whether this notebook is likely to help them. 

* **Date** That the notebook was finalised. This is just to give an indication of the currency of the notebook, and when it was last working.

* **Author** Who wrote it?

You can of course provide additional information if you choose, e.g. background, purpose etc.

As an example...

# Getting started with Sentinel 2 data

**Background** As of mid-February 2018, Sentinel 2 data is available to access within the a development environment on AWS. There are a number of things that need to be done prior to gaining access to the Sentinel 2 archive. For the purpose of this notebook, we will assume you have successfully gained access to the AWS environment where Sentinel 2 data is currently housed. 

**What does this notebook do?** This notebook steps you through how to load in and plot up data from Sentinel 2. It explores the data that are available from the Sentinel 2 satellite, and briefly describes the Sentinel satellite bands. It then loads in the ``s2a_ard_granule`` product and plots it up in true and false colour. It uses the provided pixel quality data to filters the example scene based on ``clear`` pixels. 

**Date**: February 2018.

**Author**: Claire Krause

Note on using heading levels in the Jupyter Notebooks
-----------------------------------------------------
The code that publishes the notebooks to the website uses Heading levels to grab titles and set up hyperlinks. **Please only use heading level 1 (i.e. ``#``) for the overall notebook title**. Headings throughout the notebook should use headinglevel two or below (i.e. ``##``). 

Tagging
-------

See the :doc:`Tagging Notebooks<tags>` page.

Referencing within Jupyter Notebooks
------------------------------------
Direct quotations and images from other published sources (papers, websites, textbooks) within published notebooks need to be referenced according to the GA style guide at <http://www.ga.gov.au/copyright/how-to-cite-geoscience-australia-source-of-information>

Functions using published algorithms should contain references and hyperlinks to the algorithm and paper, so users can check the assumptions prior to running analyses. 

Pushing files to the master branch for publishing
-------------------------------------------------
Protection measures put in place within the ``dea-notebooks`` repo mean that you can not simply ``push`` to the master branch. All code that you would like to publish on the ``master`` branch needs to go through a review process, which is done using a ``pull`` request. 

The process for completing a ``pull`` request may seem complicated, but is quite simple if you follow the following directions. If you are unsure, feel free to grab someone to walk you through it the first time. You will need to commit all the changes you have made to your local branch before following these steps. 

* Open a terminal window, and navigate to the ``dea-notebooks`` folder
* ``git checkout master``
* ``git pull`` (this will avoid merge conflicts later on by getting the latest version of the master branch)
* Create a new temporary branch where the files you want to publish will be placed
* ``git checkout -b <tempbranchname>`` - you can name the temp branch anything, but please include your name somewhere 
* Now you need to move the files you want to publish from your branch to this new branch
* ``git checkout <yourbranchname> -- <fileyouwanttopublish>`` This command will grab the file from your branch, and move it to this temp branch
* Repeat this for all the files you want to publish. You may need to move files around so that they sit in the four folders designated in the master branch. You can just use the file browser to do this, or use ``mv <oldlocation> <newlocation>`` from the command line
* ``git status``. You should see that you are on the temp branch, and the files you have moved across are listed in red as untracked. Double check that these files are in one of the four directories, and not in a folder of your own naming.

Updating the .rst file to point to your new files
-------------------------------------------------
Along with the code files in the repository, each folder has a ``README.rst`` file. This is the file that the DEA website uses to generate the webpage that these notebooks are being pulled in to. In order for the website to know that you have updated the repository, you need to also update the ``.rst`` file. This is super easy and can be done in any text editor. Open the ``README.rst`` file for each directory where you have added a new file. Add your new file name to the bottom of the list of files in the folder. Save and close. 

Back to the push workflow...
----------------------------

* ``git add <file>``. Repeat this for every file that you want to publish. Make sure to add the ``README.rst`` files you have updated as well!
* ``git status``. You should now see the list of files in green, ready to be committed.
* ``git commit -m "Short explanation of the files being added"``
* ``git push origin <tempbranchname>``. This will push the new branch, with the files to be published, to the remote repo. You can jump on the website and see your latest push show up on the repo in a light yellow banner below the solid red line.
* Click on ``compare & pull request`` to set up your pull request
* The ``Open a pull request`` page will show the ``base`` as ``master`` and the ``compare`` as your temp branch. If you did a pull request right up at step three, this should mean that there are no conflicts, and you can automatically merge (hopefully).
* Add a comment to the pull request, and click ``create pull request``

Approving pull requests
=======================
Anyone with admin access to the ``dea-notebooks`` repo can approve pull requests. You can see a list of the pull requests ready for review on the ``pull requests`` tab at the top of the repo. Click this tab, then click on the open pull request. You will need to review the code before you can approve the request. You can view the changes proposed and make sure that they meet the minimum metadata requirements. You do not need to check the actual code, this review process is just to check for code documentation. If the documentation looks good, click the green ``review`` button and check ``approve``. You can also request changes here if you think some key info is missing. 

Once the code has been approved, you can merge it into the ``master`` branch. Select the ``squash and merge`` option (you may need to find this in the drop down menu to the right of the green merge button. The squash and merge will squash all the commits on the temp branch into a single commit, and just make things neater. Once you have merged the new branch in, you need to **delete the branch**. There is a button on the push page that asks you if you would like to delete the now merged branch. Yes. Delete it. The changes from this branch have now been merged in, so there is no risk of losing someone's work. This will stop lots and lots of staging/temp branches from building up in the repo. 

You are now done!

Revising a pull request
-----------------------
If your reviewer suggests you make changes to code you submitted as a ``pull request``, it's easy to fix things up. Simply update your code on the same temporary branch you submitted the ``pull request`` from, commit the changes (``git commit -m "Short explanation``), push them back up to the remote repo (``git push origin <tempbranchname>``), and the new commit will automatically appear in the same ``pull request`` ready to be accepted!

Cleaning up your own repo
-------------------------
You will receive an email to the address your github account is registered with to let you know when your pull request has been approved, and then merged. Although the temp branch was deleted from the github website (the remote repo), you will still have a local copy of this branch that you will want to remove. 

``git branch`` will show you all the branches your local repo is tracking. If there are staging branches you would like to clean up, use ``git branch -d <branchtobedeleted>``. This will stop you accumulating useless branches in your local git repo.
