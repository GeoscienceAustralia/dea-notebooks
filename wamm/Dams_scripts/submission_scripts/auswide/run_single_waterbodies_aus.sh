#!/bin/bash
find /g/data/r78/cek156/dea-notebooks/WaterbodyAreaMappingandMonitoring/Timeseries/  -name *.csv > processed.txt
qsub single_get_waterbodies_aus_huge_missing.sh

