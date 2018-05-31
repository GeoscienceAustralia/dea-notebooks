#!/bin/bash

for nc in /g/data/u46/users/ext547/ewater/input_data/test/blah/*.nc
do	
	ncks -d lon,101.3,108.7 -d lat,8.9,15.7 $nc clip_$nc
	cdo setvals,0,'nan' clip_$nc nozero_$nc
	cdo addc,-273.15 nozero_$nc dc_$nc
done

