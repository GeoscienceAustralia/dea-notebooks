#/bin/bash


for ncfile in /g/data/u46/users/ext547/ewater/input_data/temperature/temperature_nc/daily_mean/*.nc; do
    echo `basename $ncfile`
    ncatted -a _FillValue,Tair,o,s,-9999 $ncfile

done
