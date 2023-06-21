#!/usr/bin/env bash

# pipe the exit code to parent process
set -ex
set -o pipefail

cd ./dea-notebooks
pip3 install ./Tools

# Test DEA Tools functions
pytest Tests/dea_tools

# Test Juputer Notebooks
pytest --durations=10 --nbval-lax Beginners_guide DEA_products How_to_guides Real_world_examples --ignore How_to_guides/External_data_ERA5_Climate.ipynb --ignore How_to_guides/Imagery_on_web_map.ipynb --ignore Real_world_examples/Estimate_climate_driver_influence_on_rainfall.ipynb --ignore Real_world_examples/Mapping_inundation_using_stream_gauges.ipynb