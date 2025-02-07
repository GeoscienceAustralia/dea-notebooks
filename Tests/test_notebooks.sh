#!/usr/bin/env bash

# Exit immediately if a command fails and show commands as they are executed
set -ex

# Set the pipefail option to ensure the script fails if any command in a pipeline fails
set -o pipefail

# Navigate to the dea-notebooks directory
cd ./dea-notebooks

# Install the DEA Tools Python package
pip3 install ./Tools

# Run the requested tests based on the parameter passed to the script
if [ -z "$1" ]; then
    # No parameter provided, run all tests
    echo "No parameter provided. Running default tests..."
    
    # Run pytest on default subset of notebooks, ignoring specific ones
    pytest --durations=10 --nbval-lax \
        Beginners_guide \
        DEA_products \
        --ignore DEA_products/DEA_Wetlands_Insight_Tool.ipynb \
        --ignore How_to_guides/Animated_timeseries.ipynb \
        --ignore How_to_guides/Contour_extraction.ipynb \
        --ignore How_to_guides/Calculating_band_indices.ipynb \
        --ignore How_to_guides/Exporting_GeoTIFFs.ipynb \
        --ignore How_to_guides/Detecting_seasonality.ipynb \
        --ignore How_to_guides/Generating_composites.ipynb \
        --ignore How_to_guides/Image_segmentation.ipynb \
        --ignore How_to_guides/Interpolation.ipynb \
        --ignore How_to_guides/Opening_GeoTIFFs_NetCDFs.ipynb \
        --ignore How_to_guides/Pansharpening.ipynb \
        --ignore How_to_guides/Planetary_computer.ipynb \
        --ignore How_to_guides/Polygon_drill.ipynb \
        --ignore How_to_guides/Principal_component_analysis.ipynb \
        --ignore How_to_guides/Rasterize_vectorize.ipynb \
        --ignore How_to_guides/Tidal_modelling.ipynb \
        --ignore How_to_guides/Using_load_ard.ipynb \
        --ignore How_to_guides/Virtual_products.ipynb \
        Real_world_examples/Coastal_erosion.ipynb \
        Real_world_examples/Intertidal_elevation.ipynb

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
    pytest --durations=100 --nbval-lax How_to_guides \
        --ignore How_to_guides/Land_cover_pixel_drill.ipynb \
        --ignore How_to_guides/External_data_ERA5_Climate.ipynb \
        --ignore How_to_guides/Imagery_on_web_map.ipynb

elif [ "$1" = "real_world_examples" ]; then
    echo "Testing Real_world_examples..."
    pytest --durations=10 --nbval-lax Real_world_examples/Coastal_erosion.ipynb Real_world_examples/Intertidal_elevation.ipynb

else
    # If an unknown parameter is provided, display a message
    echo "Unknown parameter: $1"

fi
