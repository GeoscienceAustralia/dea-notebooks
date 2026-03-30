#!/usr/bin/env bash

# Exit immediately if a command fails and show commands as they are executed
set -ex

# Set the pipefail option to ensure the script fails if any command in a pipeline fails
set -o pipefail

# Navigate to the dea-notebooks directory
cd ./dea-notebooks

# Install the DEA Tools Python package
pip3 install .

# Run the requested tests based on the parameter passed to the script
if [ -z "$1" ]; then
    # No parameter provided, run all tests
    echo "No parameter provided. Running default tests..."
    
    # Run pytest on default subset of notebooks, ignoring specific ones
    # Generating_COG_mosaics.ipynb and Detecting_seasonality.ipynb
    # temporarily removed due to S3 access bug (works on Sandbox)
    pytest --durations=20 --nbval-lax \
        Beginners_guide \
        DEA_products \
        --ignore DEA_products/DEA_Wetlands_Insight_Tool.ipynb \
        How_to_guides/Animated_timeseries.ipynb \
        How_to_guides/Contour_extraction.ipynb \
        How_to_guides/Calculating_band_indices.ipynb \
        How_to_guides/Exporting_GeoTIFFs.ipynb \
        How_to_guides/Generating_composites.ipynb \
        How_to_guides/Image_segmentation.ipynb \
        How_to_guides/Interpolation.ipynb \
        How_to_guides/Opening_GeoTIFFs_NetCDFs.ipynb \
        How_to_guides/Pansharpening.ipynb \
        How_to_guides/Planetary_computer.ipynb \
        How_to_guides/Polygon_drill.ipynb \
        How_to_guides/Principal_component_analysis.ipynb \
        How_to_guides/Rasterize_vectorize.ipynb \
        How_to_guides/Tidal_modelling.ipynb \
        How_to_guides/Using_load_ard.ipynb \
        How_to_guides/Virtual_products.ipynb \
        Real_world_examples/Coastal_erosion.ipynb \
        Real_world_examples/Intertidal_elevation.ipynb

elif [ "$1" = "dea_tools" ]; then
    echo "Testing DEA Tools..."
    pytest Tests/dea_tools

elif [ "$1" = "beginners_guide" ]; then
    echo "Testing Beginners_guide..."
    pytest --durations=20 --nbval-lax Beginners_guide

elif [ "$1" = "dea_products" ]; then
    echo "Testing DEA_products..."
    pytest --durations=20 --nbval-lax DEA_products

elif [ "$1" = "how_to_guides" ]; then
    echo "Testing How_to_guides..."
    # Detecting_seasonality, COG_overviews and Generating_COG_mosaics
    # temporarily removed due to S3 access bug (works on Sandbox)
    pytest --durations=20 --nbval-lax How_to_guides \
        --ignore How_to_guides/Land_cover_pixel_drill.ipynb \
        --ignore How_to_guides/External_data_ERA5_Climate.ipynb \
        --ignore How_to_guides/Imagery_on_web_map.ipynb \
        --ignore How_to_guides/Continental_scale_animations.ipynb \
        --ignore How_to_guides/Detecting_seasonality.ipynb \
        --ignore How_to_guides/COG_overviews.ipynb \
        --ignore How_to_guides/Generating_COG_mosaics.ipynb

elif [ "$1" = "real_world_examples" ]; then
    echo "Testing Real_world_examples..."
    pytest --durations=20 --nbval-lax Real_world_examples \
        --ignore Real_world_examples/Scalable_machine_learning \
        --ignore Real_world_examples/Estimate_climate_driver_influence_on_rainfall.ipynb \
        --ignore Real_world_examples/Mapping_inundation_using_stream_gauges.ipynb

elif [ "$1" = "scalable_machine_learning" ]; then
    echo "Testing Scalable_machine_learning..."
    pytest --durations=20 --nbval-lax Real_world_examples/Scalable_machine_learning

else
    # If an unknown parameter is provided, pass in entirely
    echo "Testing custom notebooks: $1"
    pytest --durations=20 --nbval-lax $1

fi
