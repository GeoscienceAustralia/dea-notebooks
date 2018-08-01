#/bin/bash

for ncfile in /g/data/u46/users/ext547/ewater/input_data/rainfall/rainfall_nc/three_hourly/3B42_raw_3hourly_all_data_hqp.nc; do

    echo -n .
    ncap2  -s hqp=hqp*3 $ncfile multiplied_`basename $ncfile`
    ncatted -O -a units,hqp,o,c,'mm day' multiplied_`basename $ncfile`
    ncatted -O -a long_name,hqp,o,c,'high quality precipitation (mm/day)' multiplied_`basename $ncfile`
    cdo daysum multiplied_`basename $ncfile` daily_sum_`basename $ncfile`
    cdo -splitsel,1 daily_sum_`basename $ncfile` split_
    for f in split_*.nc; do
		mytime=$(cdo showdate $f 2> /dev/null | tr -d '[:space:]')
		mv $f daily_sum_rainfall_$mytime.nc
    done
done
