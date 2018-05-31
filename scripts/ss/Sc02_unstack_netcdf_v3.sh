#!/bin/bash

for ncfile in /g/data/u46/users/ext547/ewater/input_data/test/*.nc; do
#for ncfile in /g/data/u46/users/ext547/ewater/input_data/Temperature/degrees_celcius_and_clipped/celcius/*.nc; do
	echo $ncfile

	cdo showtimestamp $ncfile >> list.txt
	cdo -splitsel,1 $ncfile split_`basename $ncfile`

	times=($(cat list.txt))

	x=0 
	for f in $(ls split_`basename $ncfile`); do 
		mv $f test_${times[$x]}.nc
		let x=$x+1
		done
	done
