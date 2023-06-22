#!/usr/bin/env bash

# pipe the exit code to the parent process
set -ex
set -o pipefail

# Install indexing tool
pip3 install --no-cache --upgrade odc-apps-dc-tools

# Setup datacube
datacube system init --no-init-users

# Clone dea-config to obtain product definition and metadata info
git clone https://github.com/GeoscienceAustralia/dea-config.git

# Setup metadata types
for metadata_yaml in $(find ./dea-config/product_metadata -name '*.yaml'); do
    datacube metadata add $metadata_yaml
done

# Index products we care about for dea-notebooks
for prod_def_yaml in $(find ./dea-config/products -name '*.yaml' -regex '.*\(ga_ls7e_nbart_gm_cyear_3\|ga_ls8c_nbart_gm_cyear_3\|ga_ls_fc_3\|ga_ls_wo_3\|ga_ls_wo_fq_cyear_3\|ga_ls_landcover_class_cyear_2\|high_tide_comp_20p\|low_tide_comp_20p\|ga_s2am_ard_3\|ga_s2bm_ard_3\|ga_ls5t_ard_3\|ga_ls7e_ard_3\|ga_ls8c_ard_3\|ga_ls9c_ard_3\).*'); do
        datacube product add $prod_def_yaml
done

datacube product list

# Index MGRS granules - Sentinel-2A
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/54/HYF/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Murray 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HBA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Murray 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Canberra 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HFB/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Canberra 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HGA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Canberra 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/55/HGB/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Canberra 4, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/56/JMQ/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Brisbane 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/56/JNQ/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Brisbane 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/54/HXK/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Menindee 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/51/KUA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Roebuck 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/51/KUV/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Roebuck 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/51/KVA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Roebuck 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2am_ard_3/51/KVV/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2am_ard_3'  # Roebuck 4, 2020

# Index MGRS granules - Sentinel-2B
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/54/HYF/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Murray 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HBA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Murray 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HFA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Canberra 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HFB/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Canberra 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HGA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Canberra 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/55/HGB/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Canberra 4, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/56/JMQ/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Brisbane 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/56/JNQ/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Brisbane 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/54/HXK/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Menindee 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/51/KUA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Roebuck 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/51/KUV/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Roebuck 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/51/KVA/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Roebuck 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_s2bm_ard_3/51/KVV/2020/*/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_s2bm_ard_3'  # Roebuck 4, 2020

# Index Landsat path/rows - Landsat 8
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/093/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Murray 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/094/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Murray 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Canberra 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/091/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Canberra 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Canberra 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/090/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Canberra 4, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/089/079/2019/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Brisbane 1, 2019
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/089/079/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Brisbane 1, 2019
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/096/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Menindee 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/095/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Menindee 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/095/083/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Menindee 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/110/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/110/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/111/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls8c_ard_3/111/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_ard_3'  # Roebuck 4, 2020

# Index Landsat path/rows - Landsat 7
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/093/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Murray 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/094/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Murray 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/091/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Canberra 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/091/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Canberra 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/090/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Canberra 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/090/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Canberra 4, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/089/079/2019/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Brisbane 1, 2019
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/089/079/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Brisbane 1, 2019
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/096/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Menindee 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/095/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Menindee 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/095/083/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Menindee 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/110/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Roebuck 1, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/110/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Roebuck 2, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/111/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Roebuck 3, 2020
s3-to-dc 's3://dea-public-data/baseline/ga_ls7e_ard_3/111/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls7e_ard_3'  # Roebuck 4, 2020

# Index Landsat path/rows - WO
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/093/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Murray 1, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/094/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Murray 2, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/091/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Canberra 1, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/091/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Canberra 2, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/090/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Canberra 3, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/090/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Canberra 4, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/089/079/2019/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Brisbane 1, 2019
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/089/079/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Brisbane 1, 2019
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/096/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Menindee 1, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/095/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Menindee 2, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/095/083/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Menindee 3, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/110/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Roebuck 1, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/110/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Roebuck 2, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/111/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Roebuck 3, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_3/1-6-0/111/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_3'  # Roebuck 4, 2020

# Index Landsat path/rows - FC
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/093/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Murray 1, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/094/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Murray 2, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/091/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Canberra 1, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/091/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Canberra 2, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/090/084/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Canberra 3, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/090/085/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Canberra 4, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/089/079/2019/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Brisbane 1, 2019
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/089/079/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Brisbane 1, 2019
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/096/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Menindee 1, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/095/082/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Menindee 2, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/095/083/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Menindee 3, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/110/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Roebuck 1, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/110/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Roebuck 2, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/111/072/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Roebuck 3, 2020
s3-to-dc 's3://dea-public-data/derivative/ga_ls_fc_3/2-5-0/111/073/2020/*/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_fc_3'  # Roebuck 4, 2020

# Index Collection 3 Albers tiles - GeoMAD 
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x39/y15/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Murray 1, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x43/y15/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Canberra 1, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x44/y15/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Canberra 2, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x44/y16/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Canberra 3, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y23/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Brisbane 1, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x49/y24/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Brisbane 2, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x37/y19/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Menindee 1, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x37/y20/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Menindee 2, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y19/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Menindee 3, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x38/y20/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Menindee 4, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x17/y36/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls8c_nbart_gm_cyear_3'  # Roebuck 1, all

# Index Collection 3 Albers tiles - WO annual summaries 
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x39/y15/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Murray 1, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x43/y15/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Canberra 1, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x44/y15/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Canberra 2, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x44/y16/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Canberra 3, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x49/y23/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Brisbane 1, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x49/y24/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Brisbane 2, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x37/y19/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Menindee 1, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x37/y20/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Menindee 2, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x38/y19/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Menindee 3, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x38/y20/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Menindee 4, all
s3-to-dc 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/1-6-0/x17/y36/*/*.json' --no-sign-request --skip-lineage --stac 'ga_ls_wo_fq_cyear_3'  # Roebuck 1, all

# Index Collection 2 Albers tiles - DEA Landcover
s3-to-dc 's3://dea-public-data/derivative/ga_ls_landcover_class_cyear_2/1-0-0/*/x_-11/y_-20/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_landcover_class_cyear_2'  # Roebuck
s3-to-dc 's3://dea-public-data/derivative/ga_ls_landcover_class_cyear_2/1-0-0/*/x_20/y_-32/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_landcover_class_cyear_2'  # Brisbane
s3-to-dc 's3://dea-public-data/derivative/ga_ls_landcover_class_cyear_2/1-0-0/*/x_9/y_-36/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_landcover_class_cyear_2'  # Menindee
s3-to-dc 's3://dea-public-data/derivative/ga_ls_landcover_class_cyear_2/1-0-0/*/x_10/y_-40/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_landcover_class_cyear_2'  # Murray 1
s3-to-dc 's3://dea-public-data/derivative/ga_ls_landcover_class_cyear_2/1-0-0/*/x_11/y_-40/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_landcover_class_cyear_2'  # Murray 2
s3-to-dc 's3://dea-public-data/derivative/ga_ls_landcover_class_cyear_2/1-0-0/*/x_15/y_-40/*.odc-metadata.yaml' --no-sign-request --skip-lineage 'ga_ls_landcover_class_cyear_2'  # Canberra

# Index tidal polygons - HLTC
s3-to-dc 's3://dea-public-data/hltc/v2.0.0/composite/high-tide/lon_121/lat_-18/*.yaml' --no-sign-request --skip-lineage 'high_tide_comp_20p'
s3-to-dc 's3://dea-public-data/hltc/v2.0.0/composite/low-tide/lon_121/lat_-18/*.yaml' --no-sign-request --skip-lineage 'low_tide_comp_20p'

# Extra bespoke locations and datasets
