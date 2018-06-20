#/bin/bash

for ncfile in /g/data/u46/users/ext547/ewater/input_data/Rainfall/3B42_raw_3hourly_all_data_hqp.nc; do
    echo -n .
    cdo daysum $ncfile daily_sum_`basename $ncfile`
done
