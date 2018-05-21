# ClassificationTools.py
"""
This file contains a set of python functions used for classifying remote sensing data.
Currently includes functions for random forest classification, but additional classifiers to be
added in near future. Available functions:

    randomforest_train
    randomforest_classify
    randomforest_eval

Last modified: March 2018
Author: Robbi Bishop-Taylor

"""

# Load modules
import os
import sys
import numpy as np
from collections import OrderedDict
from matplotlib import pyplot as plt
from osgeo import gdal
from os.path import splitext
from sklearn.ensemble import RandomForestClassifier

# Import DEA Notebooks scripts
sys.path.append('../Scripts')
from SpatialTools import layer_extent
from SpatialTools import rasterize_vector
from SpatialTools import array_to_geotiff


def randomforest_train(train_shps, train_field, data_func, data_func_params={},
                       classifier_params={}, train_reclass=None):
    '''
    Extracts training data from xarray dataset for multiple training shapefiles.
    Loops through each each training shapefile, using shapefile extent for spatial
    query. Outputs a trained classifier object and training label and data arrays.

    :attr train_shps: list of training shapefile paths to import. Each file
    should cover a small enough spatial area so as to not slow dc.load function
    excessively (e.g. 100 x 100km max)
    :attr train_field: shapefile field containing classification class
    :attr data_func: function to import xarray data for each shapefile. Should return
    an xarray dataset with 'crs' and 'affine' attributes
    :attr data_func_params: optional dict of dc.load query inputs. Useful for defining
    time query for temporal datasets (spatial queries are set automatically from shapefiles)
    :attr classifier_params: optional dict of parameters for training random forest
    :attr train_reclass: optional dict of from:to pairs to re-map shapefile field classes.
    Useful for simplifying multiple classes into a simpler set of classes

    :returns: trained classifier
    :returns: array of training labels
    :returns: array of training data
    '''

    # Output training label and pixel arrays
    training_labels_list = list()
    training_samples_list = list()

    # For each shapefile, extract datacube data using extent of points
    # and add resulting spectral data and labels to list of arrays
    for train_shp in train_shps:

        print("Importing training data from {}:".format(train_shp))

        try:

            # Open vector of training points with gdal
            data_source = gdal.OpenEx(train_shp, gdal.OF_VECTOR)
            layer = data_source.GetLayer(0)

            # Compute extents and generate spatial query
            xmin, xmax, ymin, ymax = layer_extent(layer)
            query_train = {'x': (xmin + 2000, xmax - 2000),
                           'y': (ymin + 2000, ymax - 2000),
                           'crs': 'EPSG:3577',
                           **data_func_params}
            print(query_train)

            # Import data  as xarray and extract projection/transform data
            training_xarray = data_func(query_train)
            geo_transform_train = training_xarray.affine.to_gdal()
            proj_train = training_xarray.crs.wkt

            # Covert to array and rearrange dimension order
            bands_array_train = training_xarray.to_array().values
            bands_array_train = np.einsum('bxy->xyb', bands_array_train)
            rows_train, cols_train, bands_n_train = bands_array_train.shape

            # Import training data shapefiles and convert to matching raster pixels
            training_pixels = rasterize_vector(layer, cols_train, rows_train,
                                               geo_transform_train, proj_train,
                                               field=train_field)

            # Extract matching image sample data for each labelled pixel location
            is_train = np.nonzero(training_pixels)
            training_labels = training_pixels[is_train]
            training_samples = bands_array_train[is_train]

            # Remove nans from training samples
            training_labels = training_labels[~np.isnan(training_samples).any(axis=1)]
            training_samples = training_samples[~np.isnan(training_samples).any(axis=1)]

            # Append outputs
            training_labels_list.append(training_labels)
            training_samples_list.append(training_samples)

        except AttributeError:

            print("  Skipping training data from {}; check file path".format(train_shp))

    # Combine polygon training data
    training_labels = np.concatenate(training_labels_list, axis=0)
    training_samples = np.concatenate(training_samples_list, axis=0)

    # Optionally re-map classes prior to classification training
    if train_reclass:
        # For each class in training labels, re-map to new values using train_reclass
        training_labels[:] = [train_reclass[label] for label in training_labels]

    # Set up classifier and train on training sample data and labels
    # Options for tuning: https://www.analyticsvidhya.com/blog/2015/06/tuning-random-forest-model/
    print("\nTraining random forest classifier...")
    classifier = RandomForestClassifier(**classifier_params)
    classifier.fit(training_samples, training_labels)
    print("Model trained on {0} bands and "
          "{1} training samples".format(training_samples.shape[1],
                                        str(len(training_samples))))

    return classifier, training_labels, training_samples


def randomforest_classify(classifier, analysis_data, classification_output, class_prob=False):
    '''
    Performs classification of xarray dataset using pre-trained random forest classifier,
    and export classified output to a geotiff. Optionally, also export a predicted class
    probability raster (i.e. indicating fraction of samples of the predicted class in a leaf)

    :attr classifier: random forest classifier generated using randomforest_train
    :attr analysis_data: xarray dataset with 'crs' and 'affine' attributes
    and the same number of bands as data used to train classifier
    :attr classification_output: file path to output geotiff classification
    :attr class_prob: if True, compute predicted class probability and export to
    geotiff suffixed with "_prob.tif"

    :returns: classified array and (optional) classification probability array
    '''

    geo_transform = analysis_data.affine.to_gdal()
    proj = analysis_data.crs.wkt

    # Covert to array and rearrange dimension order
    analysis_array = analysis_data.to_array().values
    analysis_array = np.einsum('bxy->xyb', analysis_array)
    rows, cols, bands_n = analysis_array.shape
    print("Data to classify:\n  Rows: {0}\n  Columns: {1}\n  Bands: {2}".format(rows, cols, bands_n))

    # Remove nodata and return flattened 'pixel x bands' array
    input_nodata = np.isnan(analysis_array).any(axis=2)
    flat_pixels = analysis_array[~input_nodata]

    # Run classification
    print("\nClassification processing...")
    result = classifier.predict(flat_pixels)

    # Restore 2D array by assigning flattened output to empty array
    classification = np.zeros((rows, cols))
    classification[~input_nodata] = result

    # Nodata removed
    print("  {} nodata cells removed".format(str(np.sum(classification == 0))))

    # Export to file
    array_to_geotiff(classification_output,
                     data=classification,
                     geo_transform=geo_transform,
                     projection=proj,
                     nodata_val=0)
    print("  Classification exported")

    # If requested, export classification probability:
    if class_prob:

        # Compute predicted class probability (fraction of samples of same class in a leaf)
        # Use max to return only highest probability (the one that determined output class)
        print("\nClass probability processing...")
        result_prob = classifier.predict_proba((flat_pixels))
        result_prob = np.max(result_prob, axis=1) * 100.0

        # Restore 2D array by assigning flattened output to empty array
        classification_prob = np.zeros((rows, cols))
        classification_prob[~input_nodata] = result_prob

        # Export to file
        array_to_geotiff(splitext(classification_output)[0] + "_prob.tif",
                         data=classification_prob,
                         geo_transform=geo_transform,
                         projection=proj,
                         nodata_val=-999)
        print("  Class probability exported")

        return classification, classification_prob

    else:

        return classification, None


def randomforest_eval(training_labels, training_samples, classifier_scenario,
                      output_path, max_estimators=100):
    """
    Takes a set of training labels and training samples, and plots OOB error against
    a range of classifier parameters to explore how parameters affect classification.

    :attr training_labels: an (X, ) array of training labels
    :attr training_samples: an (X, B) array of training sample data
    :attr classifier_scenario: dict of classifier scenarios to plot
    :attr output_path: output path for plot of OOB error by scenario
    :attr max_estimators: max number of estimators to plot on x-axis (default = 100)
    """

    # Map classifier name to list of n_estimators, error rate pairs.
    error_rate = OrderedDict((label, []) for label, _ in classifier_scenario)

    # Set min estimators to evaluate
    min_estimators = 1

    # For each classifier in pre-defined scenario
    for label, clf in classifier_scenario:

        for i in range(min_estimators, max_estimators + 1):
            clf.set_params(n_estimators=i)
            clf.fit(training_samples, training_labels)

            # Record OOB error rate
            oob_error = 1 - clf.oob_score_
            error_rate[label].append((i, oob_error))

    # Generate "OOB error rate" vs. "n_estimators" plot.
    for label, clf_err in error_rate.items():
        xs, ys = zip(*clf_err)
        plt.plot(xs, ys, label=label)

    # Plot and save output as figure
    plt.xlim(min_estimators, max_estimators)
    plt.xlabel("n_estimators")
    plt.ylabel("OOB error rate")
    plt.legend(loc="upper right")
    plt.yscale('log')
    plt.savefig(output_path, bbox_inches='tight')
    plt.show()
