#/bin/bash

for ncfile in /g/data/u46/users/ext547/ewater/input_data/test/*.nc; do
    echo -n .
    cdo daymax $ncfile max_`basename $ncfile`
done
