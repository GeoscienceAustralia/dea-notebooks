#!/usr/bin/env bash

# pipe the exit code to parent process
set -ex
set -o pipefail

cd ./dea-notebooks
pip3 install ./Tools

if [ "$#" -eq 0 ]; then
    echo "No parameter provided. Running all tests..."
    pytest --durations=10 --nbval-lax Beginners_guide DEA_products --ignore DEA_products/DEA_Wetlands_Insight_Tool.ipynb How_to_guides/Animated_timeseries.ipynb How_to_guides/Contour_extraction.ipynb How_to_guides/Calculating_band_indices.ipynb How_to_guides/Exporting_GeoTIFFs.ipynb How_to_guides/Detecting_seasonality.ipynb How_to_guides/Generating_composites.ipynb How_to_guides/Image_segmentation.ipynb How_to_guides/Interpolation.ipynb How_to_guides/Opening_GeoTIFFs_NetCDFs.ipynb How_to_guides/Pansharpening.ipynb How_to_guides/Planetary_computer.ipynb How_to_guides/Polygon_drill.ipynb How_to_guides/Principal_component_analysis.ipynb How_to_guides/Rasterize_vectorize.ipynb How_to_guides/Tidal_modelling.ipynb How_to_guides/Using_load_ard.ipynb How_to_guides/Virtual_products.ipynb Real_world_examples/Coastal_erosion.ipynb Real_world_examples/Intertidal_elevation.ipynb
elif [ "$1" = "dea_tools" ]; then
    echo "Testing DEA Tools..."
    pytest Tests/dea_tools
elif [ "$1" = "beginners_guide" ]; then
    echo "Testing Beginners_guide..."
    pytest --durations=100 --nbval-lax Beginners_guide
elif [ "$1" = "dea_products" ]; then
    echo "Testing DEA_products..."
    pytest --durations=100 --nbval-lax DEA_products
elif [ "$1" = "how_to_guides" ]; then
    echo "Testing How_to_guides..."
    pytest --durations=100 --nbval-lax How_to_guides --ignore How_to_guides/Land_cover_pixel_drill.ipynb --ignore How_to_guides/External_data_ERA5_Climate.ipynb --ignore How_to_guides/Imagery_on_web_map.ipynb
else
    echo "Unknown parameter: $1"
    ls -l
fi
