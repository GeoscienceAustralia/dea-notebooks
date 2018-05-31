#!/bin/bash


for nc in degreesC_*.nc
do
    cdo setvals,0,-9999 $nc degreesC_$nc
done
