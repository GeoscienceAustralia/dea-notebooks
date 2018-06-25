#/bin/bash


for ncfile in /g/data/u46/users/ext547/ewater/input_data/Temperature/degrees_celcius_and_clipped/celcius/original/*.nc; do
    echo `basename $ncfile`
    ncatted -a _FillValue,Tair,o,s,-9999 $ncfile

done
