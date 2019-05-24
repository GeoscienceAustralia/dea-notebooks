#!/bin/bash
find /g/data/r78/cek156/dea-notebooks/WaterbodyAreaMappingandMonitoring/Timeseries/  -name *.csv > processed.txt
qsub get_waterbodies_aus_huge_missing1.sh
qsub get_waterbodies_aus_huge_missing2.sh
qsub get_waterbodies_aus_huge_missing3.sh
