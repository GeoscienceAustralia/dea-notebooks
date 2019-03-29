#/bin/bash

for ncfile in /g/data/u46/users/ext547/ewater/input_data/laos/temp/celcius/*.nc; do
    echo -n .
    cdo daymean $ncfile mean_`basename $ncfile`
    cdo daymin $ncfile min_`basename $ncfile`
    cdo daymax $ncfile max_`basename $ncfile`
done
