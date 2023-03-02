#!/usr/bin/env bash
set -ex
set -o pipefail

pip3 install -e /tmp/dea-notebooks/Tools
cd /tmp/dea-notebooks

pytest --durations=10 --nbval-lax Beginners_guide DEA_datasets Frequently_used_code/Contour_extraction.ipynb Frequently_used_code/Calculating_band_indices.ipynb Frequently_used_code/Downloading_data_with_STAC.ipynb Frequently_used_code/Exporting_GeoTIFFs.ipynb Frequently_used_code/Generating_composites.ipynb Frequently_used_code/Image_segmentation.ipynb Frequently_used_code/Opening_GeoTIFFs_NetCDFs.ipynb Frequently_used_code/Pansharpening.ipynb Frequently_used_code/Polygon_drill.ipynb Frequently_used_code/Principal_component_analysis.ipynb Frequently_used_code/Rasterize_vectorize.ipynb Frequently_used_code/Using_load_ard.ipynb Frequently_used_code/Virtual_products.ipynb


