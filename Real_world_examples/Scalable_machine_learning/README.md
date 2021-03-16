<img align="centre" src="../../Supplementary_data/dea_logo_wide.jpg" width="100%">

# Scalable Supervised Machine Learning on the Open Data Cube

* **Prerequisites:** This notebook series assumes some familiarity with machine learning, statistical concepts, and python programming. Beginners should consider working through the earlier notebooks in the [dea-notebooks](https://github.com/GeoscienceAustralia/dea-notebooks) repository before attempting to run through this notebook series.

## Background

Classification of satellite images using supervised machine learning (ML) techniques has become a common occurence in the remote sensing literature. Machine learning offers an effective means for identifying complex land cover classes in a relatively efficient manner. However, sensibly implementing machine learning classifiers is not always straighforward owing to the training data requirements, the computational requirements, and the challenge of sorting through a proliferating number of software libraries. Add to this the complexity of handling large volumes of satellite data and the task can become unwieldy at best. 

This series of notebooks aims to lessen the difficulty of running machine learning classifiers on satellite imagery by guiding the user through the steps necessary to classify satellite data using the [Open Data Cube](https://www.opendatacube.org/) (ODC). This is achieved in two ways. Firstly, the critical steps in a ML workflow (in the context of the ODC) are broken down into discrete notebooks which are extensively documented. And secondly, a number of custom python functions have been written to ease the complexity of running ML on the ODC. These include (among others) `collect_training_data`, `spatial_cluster`, `SKCV`, and `predict_xr`, all of which are contained in the [dea_tools.classification](../../Tools/dea_tools/classification.py) package. These functions are introduced and explained further in the relevant sections of the notebooks.

There are four primary notebooks in this notebook series (along with an optional fifth notebook), that each represent a critical step in a ML workflow. 

1. `Extracting_training_data.ipynb` explores how to extract training data (feature layers) from the ODC using geometries within a shapefile (or geojson). The goal of this notebook is to familarise users with the `collect_training_data` function so you can extract the appropriate data for your use-case.
2. `Inspect_training_data.ipynb`: After having extracted training data from the ODC, its important to inspect the data using a number of statistical methods to aid in understanding if our feature layers are useful for distinguishing between classes.
3. `Evaluate_optimize_fit_classifier.ipynb`: Using the training data extracted in the first notebook, this notebook first evaluates the accuracy of a given ML model (using nested, spatial k-fold cross validation), performs a hyperparameter optimization, and then fits a model on the training data.
4. `Classify_satellite_data.ipynb`: This is where we load in satellite data and classify it using the model created in the previous notebook. The notebook initially asks you to provide a number of small test locations so we can observe visually how well the model is going at classifying real data. The last part of the notebook attempts to classify a much larger region.  
5. `Object-based_filtering.ipynb`: This notebook is provided as an optional extra. It guides you through converting your pixel-based classification into an object-based classification using image segmentation.

The default example in the notebooks uses a training dataset containing "crop" and "non-crop" labels (labelled as 1 and 0 in the geojson, respectively) from across Australia. The training data is called `"crop_training.geojson"`, and is located in the `'data/'` folder. This reference data was acquired and pre-processed from the USGS's Global Food Security Analysis Data portal [here](https://croplands.org/app/data/search?page=1&page_size=200) and [here](https://e4ftl01.cr.usgs.gov/MEASURES/GFSAD30VAL.001/2008.01.01/).  By the end of this notebook series we will have produced a model for identifying cropland areas in Australia, and we will output a cropland mask (as a geotiff) for around region around south-east WA.

If you wish to begin running your own classification workflow, the first step is to replace this training data with your own in the `Extract_training_data.ipynb` notebook. Though of course its best to run through the default example first to ensure you understand the content before altering the notebooks for your specific use case. 

**Important notes**

* There are many different methods for running ML models and the approach used here may not suit your own classification problem. This is especially true for the `Evaluate_optimize_fit_classifier.ipynb` notebook, which has been crafted to suit the default training data. It's advisable to research the different methods for evaluating and training a model to determine which approach is best for you. Remember, the first step of any scientific pursuit is to precisely define the problem. 
* The word "**Scalable**" in the title _Scalable ML on the ODC_ refers to scalability within the contraints of the machine you're running. These notebooks rely on [dask](https://dask.org/) (and [dask-ml](https://ml.dask.org/)) to manage memory and distribute the computations across mulitple cores. However, the notebooks are set up for the case of running on a single machine. For example, if your machine has 2 cores and 16 Gb of RAM (these are the specs on the default Sandbox), then you'll only be able to load and classify data up to that 16 Gb limit (and parallelization will be limited to 2 cores). Access to larger machines is required to scale analyses to very large areas. Its unlikley you'll be able to use these notebooks to classify satellite data at the country-level scale using laptop sized machines.  To better understand how we use dask, have a look at the [dask notebook](../../Beginners_guide/09_Parallel_processing_with_Dask.ipynb).

**Helpful Resources**

* There are many online courses that can help you understand the fundamentals of machine learning with python e.g. [edX](https://www.edx.org/course/machine-learning-with-python-a-practical-introduct), [coursera](https://www.coursera.org/learn/machine-learning-with-python). 
* The [Scikit-learn](https://scikit-learn.org/stable/supervised_learning.html) documentation provides information on the available models and their parameters.
* This [review article](https://www.tandfonline.com/doi/full/10.1080/01431161.2018.1433343) provides a nice overview of machine learning in the context of remote sensing.
* The stand alone notebook, [Machine_learning_with_ODC](https://github.com/GeoscienceAustralia/dea-notebooks/blob/develop/Frequently_used_code/Machine_learning_with_ODC.ipynb), in the `Real_world_examples/` folder is a companion piece to these notebooks and provides a more succint (but less descriptive) version of the workflow demonstrated here.
___


## Getting Started

To begin working through the notebooks in this `Scalable ML on the ODC` workflow, go to the first notebook `Extracting_training_data.ipynb`.


***

## Additional information

**License:** The code in this notebook is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). 
Digital Earth Africa data is licensed under the [Creative Commons by Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) license.

**Contact:** If you need assistance, please post a question on the [Open Data Cube Slack channel](http://slack.opendatacube.org/) or on the [GIS Stack Exchange](https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions [here](https://gis.stackexchange.com/questions/tagged/open-data-cube)).
If you would like to report an issue with this notebook, you can file one on [Github](https://github.com/digitalearthafrica/deafrica-sandbox-notebooks).
