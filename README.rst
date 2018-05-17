.. Notebook Gallery Instructions:

=========================
Overview of DEA Notebooks
=========================
This documentation is designed to step the user through getting started with Digital Earth Australia (DEA), through to more complicated algorithms and workflows. The intended order of these notebook folders are:

1. `Getting_started <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Getting_started>`_

2. `DEA_datasets <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/DEA_datasets>`_

3. `Integrating_external_data <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Integrating_external_data>`_

4. `Index_calculation <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Index_calculation>`_

5. `Temporal_analysis <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Temporal_analysis>`_

6. `Composite_generation <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Composite_generation>`_

7. `Image_classification <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Image_classification>`_

8. `Outputting_data <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Outputting_data>`_

9. `Workflows <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Workflows>`_

10. `Scripts <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master/Scripts>`_

If you are searching for a specific functionality, use the `Tags Index <http://geoscienceaustralia.github.io/digitalearthau/genindex.html>`_ to search for a suitable example. If there is a functionality that has not been documented that you think should be, please create an `Issue` in the `dea-notebooks repository. <https://github.com/GeoscienceAustralia/dea-notebooks/issues>`_

The basic structure of this repository is designed to keep 'all' of the DEA Jupyter notebooks in one place. The repository uses branches to manage individuals' notebooks, and to allow easy publishing of notebooks ready to be shared. There are two main types of branches:

* `Master branch <https://github.com/GeoscienceAustralia/dea-notebooks/tree/master>`_: where notebooks are put that are ready to be shared. Notebooks added to this branch will be published on the `DEA User Guide page <http://geoscienceaustralia.github.io/digitalearthau/index.html>`_. The master branch is protected, and requires changes to be approved via a ``pull request`` before changes are made to the branch. This is simply to avoid mistakes when pushing to this branch, and to allow a quick check of code before publishing. The check is basically just looking for the existence of required metadata, and that the file name has been added to the ``.rst`` index so it can be published on the `DEA User Guide page <http://geoscienceaustralia.github.io/digitalearthau/index.html>`_.

* `Working branches <https://github.com/GeoscienceAustralia/dea-notebooks/branches>`_: these are named using the owner's name as the branch name (e.g. ``ClaireK``, ``BexDunn``). These are the working spaces for people and essentially your own place to play around with. The notebooks here do not need to be pretty or even finished. It's just a place to keep everything together. It also means that if you want to collaborate on a working version of a notebook, you can easily find and share notebooks.

Getting started with DEA notebooks
==================================

To start contributing to the DEA notebooks page, first read through the `Publishing finished notebooks`_ section to ensure that your notebook meets all the metadata and formatting requirements. This should only take a few minutes, and ensures that all notebooks are thoroughly documented so that they can be understood by all users, and rendered correctly on the `DEA User Guide page <http://geoscienceaustralia.github.io/digitalearthau/index.html>`_.

Once you have checked that your notebook meets all the publishing requirements, there are two main options for interacting with ``dea-notebooks``:

* `DEA notebooks using command-line git`_: This is the recommended workflow as it makes it easy to stay up to date with the latest versions of functions and code, and makes it impossible to lose your work. 
* `DEA notebooks using Github`_: Alternatively, the Github website can be used to upload and modify the ``dea-notebooks`` repository directly. This can be a good way to get started with ``dea-notebooks`` quickly.

Finally, anyone with admin access can contribute to ``dea-notebooks`` by reviewing pull requests to ensure that changes meet minimum publishing requirements. The `Approving pull requests`_ section explains how! 


=============================
Publishing finished notebooks
=============================

Metadata requirements for publishing
====================================

The notebook name should be descriptive and contain no spaces.

To ensure that the published notebooks are actually searchable and useable, the first cell of the notebook must have the following metadata as a minimum:

* **What does this notebook do?** Include a fairly detailed description of what the notebook does. This will allow someone looking for an example of a particular functionality to decide whether this notebook is likely to help them. 

* **Date:** Date when the notebook was last modified. This is just to give an indication of the currency of the notebook, and when it was last working.

* **Author:** Who wrote it?

You can of course provide additional information if you choose, e.g. background, purpose etc. For example, from the "Getting started with Sentinel 2 data" notebook:

    **Background:** As of mid-February 2018, Sentinel 2 data is available to access within the a development environment on AWS. There are a number of things that need to be done prior to gaining access to the Sentinel 2 archive. For the purpose of this notebook, we will assume you have successfully gained access to the AWS environment where Sentinel 2 data is currently housed. 
    
    **What does this notebook do?** This notebook steps you through how to load in and plot up data from Sentinel 2. It explores the data that are available from the Sentinel 2 satellite, and briefly describes the Sentinel satellite bands. It then loads in the ``s2a_ard_granule`` product and plots it up in true and false colour. It uses the provided pixel quality data to filters the example scene based on ``clear`` pixels. 
    
    **Date**: February 2018.
    
    **Author**: Claire Krause

Heading levels in Jupyter Notebooks
===================================

The code that publishes the notebooks to the website uses Heading levels to grab titles and set up hyperlinks. **Please only use heading level 1 (i.e. `#`) for the overall notebook title**. Headings throughout the notebook should use heading level two or below (i.e. ``##``). 

Adding tags to notebooks
========================

See the `Tagging Notebooks <https://github.com/GeoscienceAustralia/dea-notebooks/blob/master/tags.rst>`_ page.

Updating the .rst file to point to your new files
=================================================

Along with the code files in the repository, each folder has a ``README.rst`` file. This is the file that the DEA website uses to generate the webpage that these notebooks are being pulled in to. In order for the website to know that you have updated the repository, you need to also update the ``.rst`` file. This can be done in any text editor. Open the ``README.rst`` file for each directory where you have added a new file. Add your new file name to the bottom of the list of files in the folder, then save and close. 

Referencing within Jupyter Notebooks
====================================

Direct quotations and images from other published sources (papers, websites, textbooks) within published notebooks should be referenced according to the `GA style guide <http://www.ga.gov.au/copyright/how-to-cite-geoscience-australia-source-of-information>`_. Functions using published algorithms should contain references and hyperlinks to the algorithm and paper, so users can check the assumptions prior to running analyses. 

Displaying widgets in Jupyter Notebooks
=======================================

When you publish a Jupyter notebook with widgets in it to `dea-notebooks`, there are two steps to getting your widgets to display.
Firstly, before you push your notebook to the repo, go to the 'Widgets' drop down menu and 'Save Notebook Widget State'. Then save your notebook before pushing it to the repo. This preserves the widget state so that you can see what the results were when the notebook is published.

**Hot Tip:** You can also use Jupyter NBviewer as a nice way to show people your notebooks. This loads far faster than Github, and can be necessary because Github doesn't render all notebook widgets properly. Go to `<https://nbviewer.jupyter.org>`_ and insert the address of your ``git`` notebook, and then put the address of the NBviewer page that is generated up top of your notebook so people can view your fancy widgets. For example:

`<https://nbviewer.jupyter.org/github/GeoscienceAustralia/dea-notebooks/blob/master/Workflows/RetrieveLandsat8ViewAndExport.ipynb>`_


====================================
DEA notebooks using command-line git
====================================

To get started with ``dea-notebooks`` using command line git, the first step is to clone this repository to a suitable location. This will most likely be a location you can access on the VDI, so you can easily work with your notebooks. Note that this repo is likely to become quite large, so make sure you have enough space in the location you clone the repository to (i.e. probably not your home directory, but your directory on ``/g/data`` should be perfect). 

To clone the repo (on the VDI):
=================================
* Navigate to the directory you want the repository to sit using a Terminal window (``cd <directory>``)
* Type ``git clone git@github.com:GeoscienceAustralia/dea-notebooks.git``
* A new folder called ``dea-notebooks`` will be created, which is a copy of the code repo
* ``cd dea-notebooks``
* Use the command ``git status`` (at any time) to check which branch you are on and any changes you have made. You should see that you are automatically on the ``master`` branch. This is the published branched of the repository. 
* To create your own branch, type ``git checkout -b <yourname>`` (where ``<yourname>`` will be the name of the new branch).
* You will automatically be changed to your new branch (you can use ``git status`` to check this). Any changes you make here will not affect the other branches of the repository. 

Setting up your own version of the repo
=======================================
You will notice that your branch of the repo contains a copy of everything in the master branch. This may not be what you actually want. You can feel free to delete everything that is automatically put in your own branch, and start from scratch with your own directory structures. 

**Note**: Make sure you are on your own branch *before* deleting everything. You can check this with ``git status``. If you happen to delete everything from the master branch, it can be restored (that's the wonder of version control), but try to avoid this in the first place.

To delete folders (or files) in a ``git`` managed repository, use ``git rm <file>``. This tells ``git`` you are deleting a file from the tracked repository, which makes things a lot cleaner when you go to commit those changes later on. If you would like to delete a whole directory, you need to add the ``-r`` (recursive) flag to the command; ``git rm -r Getting_started``. 

Committing and pushing changes to your personal branch on the online repository
====================================================================================
The new branch you have created exists in your local version of the repository, but you won't yet see it on Github because the website doesn't know about your new branch yet. To do this, you will need to commit and then "push" your changes. If you now type ``git status`` you will see two groups of files; those ``git`` is tracking and has noticed have changed since the last commit, and those ``git`` is not tracking. 

To add the new files and folders you have created to the ``git`` tracked repo, type ``git add <file or folder>``. Go through all the folders you would like ``git`` to track and ``git add`` them. Once you are ready to commit your changes, type ``git commit -m "this is a short description of the changes you have made"``. 

Even though you will probably be the only person working on your personal branch, it is good practice to type ``git pull`` prior to pushing your commit. This will make sure you have the latest version of the repository, and will hopefully avoid any potential merge conflicts when you go to push. 

Assuming ``git pull`` didn't throw up any errors, you can now push your commit. To do this, type ``git push -u origin <your branch name>``. ``git`` will now connect to the remote repository and add your commit to the Github repo. You should now be able to see your new branch on the online dea-notebooks repo. The ``-u`` switch will set up your branch to properly track the remote branch of the same name. If you do a ``git pull`` and get a message that says ``you have not told me which branch to merge with``, this is because the local and remote repos were not set up to talk to each other properly. Easy fix! Type ``git branch --set-upstream <branch> origin/<branch>``. ``git`` should now be happy.

Publishing changes to the master branch using a pull request
============================================================

The master branch of ``dea-notebooks`` is where notebooks go that you are ready to share and publish. Note that even once the notebooks are published, you can still edit and update them - this does not close them off to you for further work. 

Protection measures put in place within the ``dea-notebooks`` repo mean that you cannot simply ``push`` to the master branch. All code that you would like to publish on the ``master`` branch needs to go through a review process, which is done using a ``pull`` request. 

The process for completing a ``pull`` request may seem complicated, so if you are unsure feel free to grab someone to walk you through it the first time. You will need to commit all the changes you have made to your local branch before following these steps. 

1. Open a terminal window, and navigate to the ``dea-notebooks`` folder (e.g. ``cd dea-notebooks``)

2. ``git checkout master``

3. ``git pull`` (this will avoid merge conflicts later on by getting the latest version of the master branch)

4. Create a new temporary branch where the files you want to publish will be placed

5. ``git checkout -b <tempbranchname>`` - you can name the temp branch anything, but please include your name somewhere 

6. Now you need to move the files you want to publish from your branch to this new temporary branch

7. ``git checkout <yourbranchname> -- <fileyouwanttopublish>`` This command will grab the file from your branch, and move it to this temp branch

8. Repeat this for all the files you want to publish. You may need to move files around so that they sit in one of the ten directories (e.g. ``Getting_started``, ``DEA_notebooks``) designated in the master branch. You can just use the file browser to do this, or use ``mv <oldlocation> <newlocation>`` from the command line

9. ``git status``. You should see that you are on the temp branch, and the files you have moved across are listed in red as untracked. Double check that these files are in one of the ten ``dea-notebook`` directories, and not in a folder of your own naming.

10. ``git add <file>``. Repeat this for every file that you want to publish. Make sure to add the ``README.rst`` files you have updated as well (see the `Updating the .rst file to point to your new files`_ section above)! If you do a ``git status`` here, you should now see the list of files in green ready to be committed.

11. ``git commit -m "Short explanation of the files being added"``

12. ``git push origin <tempbranchname>``. This will push the new branch, with the files to be published, to the remote repo. You can jump on the website and see your latest push show up on the repo in a light yellow banner below the solid red line.

13. Click on ``Compare & pull request`` to set up your pull request

14. The ``Open a pull request`` page will show the ``base`` as ``master`` and the ``compare`` as your temp branch. If you did ``git pull`` at step three, this should mean that there are no conflicts, and you can automatically merge (hopefully).

15. Add a comment to the pull request, and click ``Create pull request``

Revising a pull request
=======================
If your reviewer suggests you make changes to code you submitted as a ``pull request``, it's easy to fix things up. Simply update your code on the same temporary branch you submitted the ``pull request`` from, commit the changes (``git commit -m "Short explanation"``), push them back up to the remote repo (``git push origin <tempbranchname>``), and the new commit will automatically appear in the same ``pull request`` ready to be accepted!

Cleaning up your own repo
=========================
You will receive an email to the address your Github account is registered with to let you know when your pull request has been approved, and then merged. Although the temp branch was deleted from the Github website (the remote repo), you will still have a local copy of this branch that you will want to remove. 

``git branch`` will show you all the branches your local repo is tracking. If there are staging branches you would like to clean up, use ``git branch -D <branchtobedeleted>``. This will stop you accumulating useless branches in your local ``git`` repo.


==========================
DEA notebooks using Github
==========================

Using ``git`` to manage files on ``dea-notebooks`` is highly recommended because it makes it easy to stay up to date with the latest versions of functions and code, and makes it impossible to lose your work. However, it is possible to do most tasks online on Github by uploading and modifying files directly. Just like the command line ``git`` workflow, all changes to files on the repository will need to be submitted as a “pull request” to be reviewed before being added to the ``master`` branch, but the Github will automatically guide you through this process in a reasonably straightforward way.

Getting the entire dea-notebooks directory onto your PC/VDI:
==============================================================
* On ``dea-notebooks``, click "Clone or download" on top-right.
* Click "Download ZIP" and unzip to your desired location.

Adding a new notebook or file:
==============================

1. On Github, browse to the location you would like to upload your file (e.g. ``dea-notebooks/DEA_datasets``).
2. Click "Upload files" and drag and drop or select the notebook/file.
3. At the bottom of the page, add a commit title and description outlining what you have changed. Leave the commit as "Create a new branch for this commit and start a pull request", then hit "Commit changes".
4. Finally, add any extra info on the next "Open a pull request" screen, optionally assign a reviewer, and then "Create pull request". 
5. Your changes will be submitted for review, and will be added to the ``master`` branch once accepted.

Modifying an existing notebook and update it in the repository:
===============================================================

1. Edit and save the notebook on your computer without renaming the file.
2. Follow the above "Adding a new notebook or file" instructions. Github should detect any changes to the file, and will update the file on the ``master`` branch once the “pull request” has been reviewed.
3. If you want to make multiple commits before submitting a “pull request”, that's fine: at the "Create a new branch for this commit and start a pull request" stage, edit the branch name (usually something like ``robbibt-patch-1``) to something memorable, press "Commit changes", and then when the "Open a pull request" screen appears, click back to the main ``dea-notebooks`` page without creating the “pull request”. On the ``dea-notebooks`` page, make sure your new branch is selected using the drop-down "Branch:" menu, and continue to make and commit changes ("Commit directly to the <new branchname> branch" should be automatically selected when you make the commits). When you're finally ready to submit a “pull request”, click the "New pull request" button!
4. Python scripts and plain text like readme files can be edited even more easily by opening the file on Github, then clicking "Edit this file" on the top-right. Add a commit message and submit a “pull request” as above, and the changes will be visible on the `master` branch after review.

Deleting existing files:
=========================

* Find the file you want to delete in Github, and open it by clicking on the name.
* Up the top-right, select "Delete this file".
* Add a commit message, and submit as a “pull request”. The file will disappear from the ``master`` branch after review.

**Important note:** To keep your files up to date with the ``master`` branch, ensure that you regularly re-download the repository's zip file. Just make sure you upload or back-up any changed files so that they do not get overwritten by the new files!

=======================
Approving pull requests
=======================

Anyone with admin access to the ``dea-notebooks`` repo can approve “pull requests”. You can see a list of the “pull requests” ready for review on the "pull requests" tab at the top of the repo. Click this tab, then click on the open “pull request”. You will need to review the code before you can approve the request. You can view the changes proposed and make sure that they meet the minimum metadata requirements. You do not need to check the actual code: this review process is just to check for code documentation (see the `Publishing finished notebooks`_ section above). If the documentation looks good, click the green "Review" button and click "Approve". You can also request changes here if you think some key info is missing. 

Once the code has been approved, you can merge it into the ``master`` branch. Select the "Squash and merge" option (you may need to find this in the drop down menu to the right of the green merge button. The squash and merge will squash all the commits on the temp branch into a single commit, and just make things neater. Once you have merged the new branch in, you need to **delete the branch**. There is a button on the page that asks you if you would like to delete the now merged branch. Yes. Delete it. The changes from this branch have now been merged in, so there is no risk of losing someone's work. This will stop lots and lots of staging/temp branches from building up in the repo. 
