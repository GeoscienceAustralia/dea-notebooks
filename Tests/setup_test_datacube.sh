#!/usr/bin/env bash

# pipe the exit code to the parent process
set -ex
set -o pipefail

# install indexing tool
pip3 install --no-cache --upgrade odc-apps-dc-tools

# Setup datacube
datacube system init --no-init-users

# clone dea-config
git clone https://github.com/GeoscienceAustralia/dea-config.git


# Setup metadata types
for metadata_yaml in $(find ./dea-config/product_metadata -name '*.yaml'); do
    datacube metadata add $metadata_yaml
done

# # Index products we care about for dea-notebooks
# for prod_def_yaml in $(find ./dea-config/products -name '*.yaml' -regex '.*\(ga_ls7e_nbart_gm_cyear_3\|ga_ls8c_nbart_gm_cyear_3\|ga_ls_fc_3\|ga_ls_wo_3\|ga_ls_wo_fq_cyear_3\|ga_ls_landcover_class_cyear_2\|high_tide_comp_20p\|low_tide_comp_20p\|ga_s2am_ard_3\|ga_s2bm_ard_3\|ga_ls5t_ard_3\|ga_ls7e_ard_3\|ga_ls8c_ard_3\|ga_ls9c_ard_3\).*'); do
#         datacube product add $prod_def_yaml
# done

# Index products we care about for dea-notebooks
for prod_def_yaml in $(find ./dea-config/products -name '*.yaml' -regex '.*\(ga_ls8c_ard_3\).*'); do
        datacube product add $prod_def_yaml
done

datacube product list

# # Index Landsat path/rows
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/093/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Murray 1, 2020


pg_dump -U odc -p 5432 -h postgres odc > dump.sql

# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/094/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Murray 2, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Canberra 1, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Canberra 2, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Canberra 3, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Canberra 4, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/089/079/2019/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Brisbane 1, 2019
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/089/079/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Brisbane 1, 2019
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/096/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Menindee 1, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/095/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Menindee 2, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/095/083/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Menindee 3, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/110/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 1, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/110/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 2, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/111/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 3, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/111/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 4, 2020

# # Index WO path/rows
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/093/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Murray 1, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/094/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Murray 2, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/091/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Canberra 1, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/091/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Canberra 2, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/090/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Canberra 3, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/090/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Canberra 4, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/089/079/2019/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Brisbane 1, 2019
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/089/079/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Brisbane 1, 2019
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/096/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Menindee 1, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/095/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Menindee 2, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/095/083/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Menindee 3, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/110/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Roebuck 1, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/110/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Roebuck 2, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/111/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Roebuck 3, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/111/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Roebuck 4, 2020

# # Index FC path/rows
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/093/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Murray 1, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/094/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Murray 2, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/091/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Canberra 1, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/091/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Canberra 2, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/090/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Canberra 3, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/090/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Canberra 4, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/089/079/2019/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Brisbane 1, 2019
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/089/079/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Brisbane 1, 2019
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/096/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Menindee 1, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/095/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Menindee 2, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/095/083/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Menindee 3, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/110/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Roebuck 1, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/110/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Roebuck 2, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/111/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Roebuck 3, 2020
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/111/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Roebuck 4, 2020

# # Index Sentinel-2 granules
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/54/HYF/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Murray 1, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HBA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Murray 2, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Canberra 1, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Canberra 2, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HGA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Canberra 3, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HGB/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Canberra 4, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/56/JMQ/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Brisbane 1, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/56/JNQ/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Brisbane 2, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/54/HXK/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Menindee 1, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/51/KUA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Roebuck 1, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/51/KUV/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Roebuck 2, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/51/KVA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Roebuck 3, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/51/KVV/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Roebuck 4, 2020

# Index GeoMAD Collection 3 albers tiles
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x39/y15/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Murray 1, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x43/y15/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Canberra 1, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x44/y15/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Canberra 2, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x44/y16/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Canberra 3, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y23/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Brisbane 1, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y24/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Brisbane 2, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x37/y19/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Menindee 1, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x37/y20/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Menindee 2, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y19/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Menindee 3, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y20/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Menindee 4, all
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x17/y36/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Roebuck 1, all






# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y24/2017--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls7e_nbart_gm_cyear_3/3-0-0/x49/y23/2015--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls7e_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls7e_nbart_gm_cyear_3/3-0-0/x49/y24/2015--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls7e_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y23/2013--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y23/2014--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y23/2016--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y23/2017--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y24/2013--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y24/2014--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y24/2015--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y24/2016--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y19/2017--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y19/2018--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y19/2016--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y19/2015--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y19/2019--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y19/2020--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls8c_nbart_gm_cyear_3'

# # Index FC
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/096/084/1993/10/30/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/097/083/1993/11/06/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'

# # Index WO
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/096/084/1993/10/30/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/097/083/1993/11/06/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/112/082/1996/11/08/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/112/082/1996/09/05/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x37/y19/2000--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_wo_fq_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x37/y20/2000--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_wo_fq_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x38/y19/2000--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_wo_fq_cyear_3'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x38/y20/2000--P1Y/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_wo_fq_cyear_3'

# # Index Landcover
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_landcover_class_cyear_2/1-0-0/2019/x_-11/y_-20/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_landcover_class_cyear_2'
# s3-to-dc 's3://dea-public-data/derivative/ga_ls_landcover_class_cyear_2/1-0-0/2020/x_-11/y_-20/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_landcover_class_cyear_2'

# # Index HLTC
# s3-to-dc 's3://dea-public-data/hltc/v2.0.0/composite/high-tide/lon_121/lat_-18/*.yaml' --no-sign-request --skip-lineage 'high_tide_comp_20p'
# s3-to-dc 's3://dea-public-data/hltc/v2.0.0/composite/low-tide/lon_121/lat_-18/*.yaml' --no-sign-request --skip-lineage 'low_tide_comp_20p'

# # Index Sentinel-2
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/54/KVF/2019/12/16/20191216T020938/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/54/KWF/2020/03/15/20200315T022254/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/LBD/2018/09/09/20180909T020622/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/LBD/2018/09/19/20180919T021041/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/LBD/2018/09/29/20180929T020742/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/56/JNP/2018/01/06/20180107T005153/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/56/JNP/2018/01/26/20180127T005657/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/56/JNP/2018/01/16/20180117T011158/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/LBD/2018/10/09/20181009T021157/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/LBD/2018/10/19/20181019T021416/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/LBD/2018/10/29/20181029T021107/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/LBD/2018/11/08/20181108T021044/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/LBD/2018/11/18/20181118T021103/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/LBD/2018/11/28/20181128T020701/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFA/2020/09/06/20200906T012214/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2020/09/06/20200906T012214/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFA/2020/09/16/20200916T012052/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2020/09/16/20200916T012052/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFA/2020/09/26/20200926T011940/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2020/09/26/20200926T011940/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFA/2020/10/16/20201016T013401/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2020/10/16/20201016T013401/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFA/2020/10/26/20201026T013415/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2020/10/26/20201026T013415/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2021/07/13/20210713T013245/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2021/07/03/20210703T013119/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2021/08/02/20210802T012241/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2021/08/12/20210812T012257/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2021/07/23/20210723T012342/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HFB/2021/07/08/20210708T011433/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HFB/2021/06/28/20210628T011211/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HFB/2021/08/07/20210807T010152/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HFA/2021/07/28/20210728T010531/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HFA/2021/08/07/20210807T010152/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'

# # Index Landsat
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/084/2020/05/07/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/084/2020/08/27/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/084/2020/10/14/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/085/2020/05/07/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/085/2020/08/27/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/085/2020/09/28/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2020/01/07/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2020/01/23/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2020/02/24/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2020/03/11/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2020/05/14/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2020/10/21/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2020/12/08/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/084/2021/06/27/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2021/08/05/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/084/2021/07/29/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/085/2021/07/13/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/090/084/2020/07/02/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/091/084/2021/07/12/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/091/084/2021/07/28/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/090/085/2021/07/21/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/090/084/2021/08/06/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'
# s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/090/084/2021/07/05/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'

# # Additional Landsat 8 test scenes for coastal tests
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/111/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 1, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/110/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 2, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/111/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 3, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/110/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 4, 2020
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/089/079/2019/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Brisbane, 2019
# s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/089/079/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Brisbane, 2020