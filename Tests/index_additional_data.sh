#!/usr/bin/env bash
set -ex

# index products not in current db
# i.e. datacube product add ls8c_.ard

# index datasets not in current db
# i.e. # s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/111/073/2021/02/23/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
