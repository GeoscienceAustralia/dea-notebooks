#!/bin/bash

output_name="refactor"

for study_area in 4972 4973 5074 5075 4764 4765 4867 5176 5177 4870 4662 4663 4665 4767 4664 4766 4868 5377 5073 5175 5174 5276 4869 4971 5275 5277 5378 5376 4763 4252 4354 4456 4457 4871 986 3741 3742 4149 4251 1096 1198 1710 1197 1299 1196 1298 2727 1506 1507 1812 2625 1811 1608 1609 2421 1912 1913 2014 2015 2523 2726 2828 2829 2319 4970 2928 2929 3030 3031 2827 1711 2116 2115 2217 2218 2013 1302 1404 466 467 3132 3029 3131 3843 3844 2626 4355 4150 3233 2422 2524 4047 5280 5281 5382 5383 5278 5380 5381 2728 5375 5282 5379 5279 5178 5179 5180 673 571 570 468 674 5384 777 5485 1303 1405 1199 1200 1301 776 985 778 1097 882 1098 984 880 779 5483 5484 5482 677 678 780 3945 3946 4048 676 1813 2830 3640 2320 3538 3539 3641 3437 3335 3436 2423 5480 5479 5478 5481 5076 5077 4560 4458 4768 4769
              
do

    PBS="#!/bin/bash\n\
    #PBS -N ${study_area}_${output_name}\n\
    #PBS -o DEACoastLines_${study_area}_${output_name}.out\n\
    #PBS -e DEACoastLines_${study_area}_${output_name}.err\n\
    #PBS -l storage=gdata/v10+gdata/r78+gdata/xu18+gdata/fk4\n\
    #PBS -P r78\n\
    #PBS -q hugemem\n\
    #PBS -l walltime=06:00:00\n\
    #PBS -l mem=64GB\n\
    #PBS -l jobfs=2GB\n\
    #PBS -l ncpus=1\n\
    #PBS -l wd\n\
    module use /g/data/v10/public/modules/modulefiles\n\
    module load dea/unstable\n\
    module load otps\n\
    python3 /g/data/r78/rt1527/dea-notebooks/MAHTS/deacoastlines_generation.py $study_area $output_name"

    echo -e ${PBS} | qsub || echo "${study_area} failed" >> log.txt
    sleep 0.2
    echo "Submitting study area $study_area $output_name"

done

