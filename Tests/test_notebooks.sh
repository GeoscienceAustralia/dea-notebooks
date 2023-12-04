#!/usr/bin/env bash

# pipe the exit code to parent process
set -ex
set -o pipefail

cd ./dea-notebooks
pip3 install ./Tools

# Test DEA Tools functions
pytest Tests/dea_tools

# Test Juputer Notebooks
pytest --durations=10 --nbval-lax Beginners_guide
