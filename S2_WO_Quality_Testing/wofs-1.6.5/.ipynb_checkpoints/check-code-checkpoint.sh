#!/usr/bin/env bash

set -eu
set -x

# Fix me in later PR
black --check . || true

pytest tests
