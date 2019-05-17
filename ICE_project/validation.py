#!/usr/bin/env python
# coding: utf-8

# ## Validation of irrigated extent
# Generating a confusion matrix
# 
# Relying on Claire Krause's notebook for guidance:
# 
# https://github.com/GeoscienceAustralia/dea-notebooks/blob/ClaireK/Crop_mapping/NamoiPilotProjectWorkflow/ValidateAutomaticIrrigatedCropAreaGeotiffs.ipynb

import numpy as np
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt

#import custom functions
import sys
sys.path.append('src')
import DEAPlotting, SpatialTools
from transform_tuple import transform_tuple


## User Inputs

#provide the filepaths to the irrigated cropping extent tif and the validation shapefile
irrigated = "/g/data/r78/cb3058/dea-notebooks/ICE_project/results/nmdb/nmdb_Summer1993_94/nmdb_Summer1993_94_multithreshold_masked.tif"

validation = "/g/data/r78/cb3058/dea-notebooks/ICE_project/data/spatial/merged_IrrigatedCrop_1993110.shp"

clip_shp = "/g/data/r78/cb3058/dea-notebooks/ICE_project/data/spatial/validation_boundary.shp"

#what year are we validating
year = '1993-94'


#----------script proper-----------------------------------------------------------

#open the irrigatation tif
irr  = xr.open_rasterio(irrigated).drop('band').squeeze()
#grab some transform info from it
transform, projection = transform_tuple(irr, (irr.x, irr.y), epsg=3577)
width,height = irr.shape
#rasterize the catchment boundaries that encompass our validation area
boundary = SpatialTools.rasterize_vector(clip_shp, height, width,
                                         transform, projection, raster_path=None)
#clip extent to the catchment boundaries
irr = irr.where(boundary)
#convert to a boolean array of irr/not-irr
AutomaticCropBoolean  = np.isfinite(irr.values)


#convert validation shapefile to array first
ValidationMaskBoolean  = SpatialTools.rasterize_vector(validation, height, width,
                                            transform, projection, raster_path=None)
# ValidationMaskBoolean = np.where(boundary, ValidationMaskBoolean, 0
ValidationMaskBoolean = ValidationMaskBoolean.astype(bool)


# #### Compare the boolean arrays to create a confusion matrix

YesRealYesAuto = np.logical_and(AutomaticCropBoolean, ValidationMaskBoolean)
NoRealNoAuto = np.logical_and(~AutomaticCropBoolean, ~ValidationMaskBoolean)

YesRealNoAuto = np.logical_and(AutomaticCropBoolean, ~ValidationMaskBoolean)
NoRealYesAuto = np.logical_and(~AutomaticCropBoolean, ValidationMaskBoolean)


Correct_positives = YesRealYesAuto.sum()
Incorrect_positives = NoRealYesAuto.sum()
Correct_negatives = NoRealNoAuto.sum()
Incorrect_negatives = YesRealNoAuto.sum()

Totalpixels = (width * height)

Accuracy = (Correct_positives + Correct_negatives) / Totalpixels
Misclassification_rate = (Incorrect_positives + Incorrect_negatives) / Totalpixels
True_Positive_Rate = Correct_positives / ValidationMaskBoolean.sum()
False_Positive_Rate = Correct_positives / ((~ValidationMaskBoolean).sum())
Specificity = Correct_negatives / ((~ValidationMaskBoolean).sum())
Precision = Correct_positives / AutomaticCropBoolean.sum()
Prevalence = (ValidationMaskBoolean.sum() ) / Totalpixels

print('\033[1m' + '{0} Irrigated Crop Extent'.format(year) + '\033[0m')
print('Accuracy = %.5f' % Accuracy)
print('Misclassification_rate = %.5f' % Misclassification_rate)
print('True_Positive_Rate = %.5f' % True_Positive_Rate)
print('False_Positive_Rate = %.5f' % False_Positive_Rate)
print('Specificity = %.5f' % Specificity)
print('Precision = %.5f' % Precision)
print('Prevalence = %.5f' % Prevalence)

# plt.figure()
# plt.scatter(False_Positive_Rate, True_Positive_Rate)
# plt.xlim ([0, 1]);
# plt.ylim ([0, 1]);
# plt.xlabel('False Positive Rate');
# plt.ylabel('True Positive Rate');
