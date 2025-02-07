#!/usr/bin/env bash

# pipe the exit code to parent process
set -ex
set -o pipefail

cd ./dea-notebooks
pip3 install ./Tools

# Test Juputer Notebooks
pytest --durations=100 --nbval-lax DEA_products
