#!/bin/sh

docker pull opendatacube/datacube-tests:latest

# Null out the entrypoint since we aren't (yet) connecting to a database
docker run --rm -v "$PWD":/tmp/wofs -w /tmp/wofs \
opendatacube/datacube-tests:latest /bin/sh -c "pip3 install dist/*.whl && ./check-code.sh"
