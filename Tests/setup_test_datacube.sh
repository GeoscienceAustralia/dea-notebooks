#!/usr/bin/env bash
set -ex

# Setup datacube
docker-compose exec -T index datacube system init --no-default-types --no-init-users
# Setup metadata types
docker-compose exec -T index datacube metadata add "$METADATA_CATALOG"
# Index products we care about for dea-waterbodies
docker-compose exec -T index wget "$PRODUCT_CATALOG" -O product_list.csv

docker-compose exec -T index bash -c "tail -n+2 product_list.csv | grep 'ls7_nbart_geomedian_annual\|ls8_nbart_geomedian_annual\|ga_ls_wo_3\|s2a_ard_granule\|s2b_ard_granule\|ga_ls5t_ard_3\|ga_ls7e_ard_3\|ga_ls8c_ard_3\|wofs_annual_summary' | awk -F , '{print \$2}' | xargs datacube -v product add" 

# Index scenes
cat > index_tiles.sh <<EOF
s3-to-dc 's3://dea-public-data/geomedian-australia/v2.1.0/L7/x_20/y_-32/2015/01/01/*.yaml' --no-sign-request --skip-lineage 'ls7_nbart_geomedian_annual'
s3-to-dc 's3://dea-public-data/geomedian-australia/v2.1.0/L8/x_20/y_-32/2013/01/01/*.yaml' --no-sign-request --skip-lineage 'ls8_nbart_geomedian_annual'
s3-to-dc 's3://dea-public-data/geomedian-australia/v2.1.0/L8/x_20/y_-32/2014/01/01/*.yaml' --no-sign-request --skip-lineage 'ls8_nbart_geomedian_annual'
s3-to-dc 's3://dea-public-data/geomedian-australia/v2.1.0/L8/x_20/y_-32/2015/01/01/*.yaml' --no-sign-request --skip-lineage 'ls8_nbart_geomedian_annual'
s3-to-dc 's3://dea-public-data/geomedian-australia/v2.1.0/L8/x_20/y_-32/2016/01/01/*.yaml' --no-sign-request --skip-lineage 'ls8_nbart_geomedian_annual'
s3-to-dc 's3://dea-public-data/geomedian-australia/v2.1.0/L8/x_20/y_-32/2017/01/01/*.yaml' --no-sign-request --skip-lineage 'ls8_nbart_geomedian_annual'
EOF

cat index_tiles.sh | docker-compose exec -T index bash
