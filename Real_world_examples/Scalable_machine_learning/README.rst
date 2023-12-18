.. Notebook Gallery Instructions:

.. image:: ../../Supplementary_data/dea_logo_wide.jpg
  :width: 900
  :alt: Digital Earth Australia logo


Scalable Supervised Machine Learning on the Open Data Cube
==========================================================

-  **Prerequisites:** This notebook series assumes some familiarity with
   machine learning, statistical concepts, and python programming.
   Beginners should consider working through the earlier notebooks in
   the
   `dea-notebooks <https://github.com/GeoscienceAustralia/dea-notebooks>`__
   repository before attempting to run through this notebook series.

**Background**

Classification of satellite images using supervised machine learning
(ML) techniques has become a common occurrence in the remote sensing
literature. Machine learning offers an effective means for identifying
complex land cover classes in a relatively efficient manner. However,
sensibly implementing machine learning classifiers is not always
straightforward owing to the training data requirements, the
computational requirements, and the challenge of sorting through a
proliferating number of software libraries. Add to this the complexity
of handling large volumes of satellite data and the task can become
unwieldy at best.

This series of notebooks aims to lessen the difficulty of running
machine learning classifiers on satellite imagery by guiding the user
through the steps necessary to classify satellite data using the `Open
Data Cube <https://www.opendatacube.org/>`__ (ODC). This is achieved in
two ways. Firstly, the critical steps in a ML workflow (in the context
of the ODC) are broken down into discrete notebooks which are
extensively documented. And secondly, a number of custom python
functions have been written to ease the complexity of running ML on the
ODC. These include (among others) ``collect_training_data``,
and ``predict_xr``, both of which are contained in the
`dea\_tools.classification <../../Tools/dea_tools/classification.py>`__
package. These functions are introduced and explained further in the
relevant sections of the notebooks.

There are four primary notebooks in this notebook series (along with an
optional fifth notebook) that each represent a critical step in a ML
workflow.

1. ``1_Extract_training_data.ipynb`` explores how to extract training
   data (feature layers) from the ODC using geometries within a
   shapefile (or geojson). The goal of this notebook is to familiarise
   users with the ``collect_training_data`` function so you can extract
   the appropriate data for your use-case.
2. ``2_Inspect_training_data.ipynb``: After having extracted training data
   from the ODC, its important to inspect the data using a number of
   statistical methods to aid in understanding if our feature layers are
   useful for distinguishing between classes.
3. ``3_Evaluate_optimize_fit_classifier.ipynb``: Using the training data
   extracted in the first notebook, this notebook first evaluates the
   accuracy of a given ML model (using nested, k-fold cross
   validation), performs a hyperparameter optimization, and then fits a
   model on the training data.
4. ``4_Classify_satellite_data.ipynb``: This is where we load in satellite
   data and classify it using the model created in the previous
   notebook. The notebook initially asks you to provide a number of
   small test locations so we can observe visually how well the model is
   going at classifying real data. The last part of the notebook
   attempts to classify a much larger region.
5. ``5_Object-based_filtering.ipynb``: This notebook is provided as an
   optional extra. It guides you through converting your pixel-based
   classification into an object-based classification using image
   segmentation.

The default example in the notebooks uses a training dataset containing
"crop" and "non-crop" labels (labelled as 1 and 0 in the geojson,
respectively) from across Western Australia. The training data is called
``"crop_training_WA.geojson"``, and is located in the ``'data/'``
folder. This reference data was acquired and pre-processed from the
USGS's Global Food Security Analysis Data portal
`here <https://croplands.org/app/data/search?page=1&page_size=200>`__
and
`here <https://e4ftl01.cr.usgs.gov/MEASURES/GFSAD30VAL.001/2008.01.01/>`__.
By the end of this notebook series we will have produced a model for
identifying cropland areas in Western Australia, and we will output a
cropland mask (as a GeoTIFF) for around region around south-east WA.

If you wish to begin running your own classification workflow, the first
step is to replace this training data with your own in the
``1_Extract_training_data.ipynb`` notebook. However, it is best to run
through the default example first to ensure you understand the content
before altering the notebooks for your specific use case.

**Important notes**

-  There are many different methods for running ML models and the
   approach used here may not suit your own classification problem. This
   is especially true for the ``3_Evaluate_optimize_fit_classifier.ipynb``
   notebook, which has been crafted to suit the default training data.
   It's advisable to research the different methods for evaluating and
   training a model to determine which approach is best for you.
   Remember, the first step of any scientific pursuit is to precisely
   define the problem.
-  The word "**Scalable**\ " in the title *Scalable Supervised Machine Learning on the Open Data Cube*
   refers to scalability within the constraints of the machine you're
   running. These notebooks rely on `dask <https://dask.org/>`__ (and
   `dask-ml <https://ml.dask.org/>`__) to manage memory and distribute
   the computations across multiple cores. However, the notebooks are
   set up for the case of running on a single machine. For example, if
   your machine has 2 cores and 16 Gb of RAM (these are the specs on the
   default Sandbox), then you'll only be able to load and classify data
   up to that 16 Gb limit (and parallelization will be limited to 2
   cores). Access to larger machines is required to scale analyses to
   very large areas. Its unlikely you'll be able to use these notebooks
   to classify satellite data at the country-level scale using laptop
   sized machines. To better understand how we use dask, have a look at
   the `dask
   notebook <https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Beginners_guide/09_Parallel_processing_with_Dask.ipynb>`__.

**Helpful resources**

-  There are many online courses that can help you understand the
   fundamentals of machine learning with python e.g.
   `edX <https://www.edx.org/course/machine-learning-with-python-a-practical-introduct>`__,
   `coursera <https://www.coursera.org/learn/machine-learning-with-python>`__.
-  The
   `Scikit-learn <https://scikit-learn.org/stable/supervised_learning.html>`__
   documentation provides information on the available models and their
   parameters.
-  This `review
   article <https://www.tandfonline.com/doi/full/10.1080/01431161.2018.1433343>`__
   provides a nice overview of machine learning in the context of remote
   sensing.
-  The stand alone notebook,
   `Machine\_learning\_with\_ODC <https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/How_to_guides/Machine_learning_with_ODC.ipynb>`__,
   in the ``Real_world_examples/`` folder is a companion piece to these
   notebooks and provides a more succinct (but less descriptive) version
   of the workflow demonstrated here.

**Getting started**

To begin working through the notebooks in this ``Scalable Supervised Machine Learning on the Open Data Cube`` guide, go to the first ``Extracting training data from the ODC`` notebook:

.. toctree::
   :maxdepth: 1
   :caption: Scalable Supervised Machine Learning on the Open Data Cube

   1_Extract_training_data.ipynb
   2_Inspect_training_data.ipynb
   3_Evaluate_optimize_fit_classifier.ipynb
   4_Classify_satellite_data.ipynb
   5_Object-based_filtering.ipynb

--------------

**Additional information**

**License:** The code in this notebook is licensed under the `Apache
License, Version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>`__.
Digital Earth Australia data is licensed under the `Creative Commons by
Attribution 4.0 <https://creativecommons.org/licenses/by/4.0/>`__
license.

**Contact:** If you need assistance, please post a question on the `Open
Data Cube Slack channel <http://slack.opendatacube.org/>`__ or on the
`GIS Stack
Exchange <https://gis.stackexchange.com/questions/ask?tags=open-data-cube>`__
using the ``open-data-cube`` tag (you can view previously asked
questions
`here <https://gis.stackexchange.com/questions/tagged/open-data-cube>`__).
If you would like to report an issue with this notebook, you can file
one on
`Github <https://github.com/GeoscienceAustralia/dea-notebooks/>`__.
