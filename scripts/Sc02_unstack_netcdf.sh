#!/bin/bash

for ncfile in /g/data/u46/users/ext547/ewater/input_data/test/*.nc; do
	echo $ncfile
	cdo -splitsel,1 $ncfile split_
	for f in split_*.nc; do
		mytime=$(cdo showtimestamp $f 2> /dev/null | tr -d '[:space:]')
		mv $f PET_$mytime.nc
	done

done


