** Use dea-statistics to generate the NDVI composite .tifs for the study area **

** Generate raster masks of the Land use polygons and NSW validation datasets **
1. CreateRasterMaskUsingNSWValidationShapefiles.ipynb
2. CreateRasterMaskUsingNSWLUM2013Shapefile.ipynb

** Determine a suitable threshold for irrigated vs non-irrigated crop extent **
3. ApplyValidationMaskAndExaminePopulations.ipynb

** Generate the automatic irrigated crop extent from max NDVI **
4. ProduceAutomaticIrrigatedCropExtentRasters.ipynb

** Test the automatic product against the validation datasets **
5. ValidateAutomaticIrrigatedCropAreaGeotiffs.ipynb
