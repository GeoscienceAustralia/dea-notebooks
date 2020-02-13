# ClassificationTools.py
"""
This file contains a set of python functions used for classifying remote sensing data.
Currently includes functions for random forest classification, but additional classifiers to be
added in near future. Available functions:

    randomforest_train
    randomforest_classify
    randomforest_eval


"""

# Load modules
import os
import gdal
import xarray as xr
import numpy as np
from affine import Affine
from collections import OrderedDict
from rasterio.features import rasterize
from matplotlib import pyplot as plt
from datacube.helpers import write_geotiff
from osgeo import gdal
from os.path import splitext
from sklearn.ensemble import RandomForestClassifier
import geopandas as gpd

import sys
sys.path.append('../Scripts')
from dea_datahandling import array_to_geotiff
    
def randomforest_train(train_shps, train_field, xarray_data,
                       classifier_params={}, train_reclass=None):
    
    '''
    Extracts training data from xarray dataset for multiple training shapefiles. Loops through 
    each each training shapefile, using shapefile extent for spatial query, and outputs a trained 
    classifier object and training label and data arrays.
    
    Shapefiles must cover a relatively small spatial area so as to not slow dc.load function 
    excessively or use excessive memory (e.g. 30 x 30km max). If this is not the case, break your 
    shapefiles into smaller spatial subsets that can be run individually without using too much 
    memory.
    
    :param train_shps: 
        A list of training shapefile paths to import. Each file should cover a small enough spatial 
        area so as to not slow dc.load function excessively (e.g. 30 x 30km max).
    
    :param train_field: 
        A string giving the shapefile field name that contains the classification class. Classes
        must be integers for the classification to work. If your classes are strings, use the 
        `train_reclass` parameter to re-map strings to integers. 
    
    :param data_func: 
        The function used to import xarray data for each shapefile. Must return an xarray dataset 
        with 'crs' and 'affine' attributes.
    
    :param data_func_params: 
        An optional dict of dc.load query inputs. Useful for defining time query for temporal 
        datasets (spatial queries are set automatically from shapefiles).
    
    :param classifier_params: 
        An optional dict of parameters for training the random forest model.
    
    :param train_reclass: 
        An optional dict of from:to pairs to re-map shapefile field classes, which can be useful 
        for simplifying multiple classes into a simpler set of classes, or converting categorical
        /string classes into integers. For example, `train_reclass = {'water':1, 'nonwater':2}` 
        will set every 'water' class to a value of 1, and every 'nonwater' class to a value of 2.
    
    :returns: 
        A trained classifier object used as input to randomforest_classify
        
    :returns: 
        An array of training labels
        
    :returns: 
        An array of training data
        
    '''
    

    # Output training label and pixel arrays
    training_labels_list = list()
    training_samples_list = list()

    # For each shapefile, extract datacube data using extent of points
    # and add resulting spectral data and labels to list of arrays
    for train_shp in train_shps:

        print("Importing training data from {}:".format(train_shp))

        # Open vector of training points with gdal
        train_shp = train_shps[0]   
        training_gpd = gpd.read_file(train_shp)
        
        # Test if train_field is an integer, and if not, whether train_reclass is specified
        if training_gpd[train_field].dtype != np.int64 and not train_reclass:
            
            print("'train_field' is not an integer, and 'train_reclass' is not provided. Please use " \
                  "'train_reclass' to re-map the class names in your shapefile to integers (e.g. " \
                  "'train_reclass = {'water':1, 'nonwater':2}')")
        else:
            
            # If training_reclass is specified, convert values in field
            if train_reclass:
                training_gpd[train_field] = [train_reclass[i] for i in training_gpd[train_field]]
                training_gpd.to_file('training_data_reclassed.shp')
                train_shps = 'training_data_reclassed.shp'

            #open training data
            training_xarray_all = xr.open_dataset(xarray_data)
            training_xarray = training_xarray_all.drop('crs')
            # Covert to array and rearrange dimension order
            bands_array_train = training_xarray.to_array().values
            bands_array_train = np.einsum('bxy->xyb', bands_array_train)
            rows_train, cols_train, bands_n_train = bands_array_train.shape

            # update the relevant parts of the profile
            meta = {'crs': str(training_xarray_all.crs.crs_wkt),
                    'transform': training_xarray_all.crs.GeoTransform,
                    'affine':  Affine.from_gdal(*training_xarray_all.crs.GeoTransform),
                    'width': cols_train,
                    'height': rows_train,
                    'driver': 'GTiff',
                    'count': 1,
                    'dtype': 'float32'}
            
            #rasterize the vector
            rows,cols = (len(training_xarray.y), len(training_xarray.x))
            shape = zip(training_gpd['geometry'], training_gpd[train_field])
            training_pixels = rasterize(shape, 
                                        out_shape=(rows,cols),
                                        transform= meta['affine'])
            
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

        
        if len(training_labels_list) > 0:

            # Combine polygon training data
            training_labels = np.concatenate(training_labels_list, axis=0)
            training_samples = np.concatenate(training_samples_list, axis=0)

            # Set up classifier and train on training sample data and labels
            # Options for tuning: https://www.analyticsvidhya.com/blog/2015/06/tuning-random-forest-model/
            print("\nTraining random forest classifier...")
            classifier = RandomForestClassifier(**classifier_params)
            classifier.fit(training_samples, training_labels)
            print("Model trained on {0} bands and "
                  "{1} training samples".format(training_samples.shape[1],
                                                str(len(training_samples))))

            return classifier, training_labels, training_samples
        
        else:
            
            print('No classifier object or output training labels and data exported')
            

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
    geo_transform = analysis_data.crs.GeoTransform
    proj = analysis_data.crs.crs_wkt
    analysis_data = analysis_data.drop('crs')
    
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

# If the module is being run, not being imported! 
# to do this, do the following
# run {modulename}.py)

if __name__=='__main__':
#print that we are running the testing
    print('Testing..')
#import doctest to test our module for documentation
    import doctest
    doctest.testmod()
    print('Testing done')
