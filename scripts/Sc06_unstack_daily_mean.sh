#!/bin/bash

for ncfile in /g/data/u46/users/ext547/ewater/input_data/Temperature/degrees_celcius_and_clipped/celcius/original/*.nc; do
	echo $ncfile
	cdo daymean $ncfile split_
	for f in split_*.nc; do
		mytime=$(cdo showtimestamp $f 2> /dev/null | tr -d '[:space:]')
		mv $f Daily_mean_PET_$mytime.nc
	done

done



