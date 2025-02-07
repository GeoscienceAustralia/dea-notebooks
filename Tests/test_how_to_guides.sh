#!/usr/bin/env bash

# pipe the exit code to parent process
set -ex
set -o pipefail

cd ./dea-notebooks
pip3 install ./Tools

# Test Juputer Notebooks
pytest --durations=100 --nbval-lax How_to_guides --ignore How_to_guides/Land_cover_pixel_drill.ipynb --ignore How_to_guides/External_data_ERA5_Climate.ipynb --ignore How_to_guides/Imagery_on_web_map.ipynb