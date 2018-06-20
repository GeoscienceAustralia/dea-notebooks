#/bin/bash

for ncfile in /g/data/u46/users/ext547/ewater/input_data/test/*.nc; do
    echo -n .
    cdo daymin $ncfile min_`basename $ncfile`
done
