#!/bin/bash

output_name="dask"

for study_area in 3742
                  
do

    PBS="#!/bin/bash\n\
    #PBS -N ${study_area}_${output_name}\n\
    #PBS -o DEACoastLines_${study_area}_${output_name}.out\n\
    #PBS -e DEACoastLines_${study_area}_${output_name}.err\n\
    #PBS -l storage=gdata/v10+gdata/r78+gdata/xu18+gdata/fk4\n\
    #PBS -P r78\n\
    #PBS -q normal\n\
    #PBS -l walltime=12:00:00\n\
    #PBS -l mem=64GB\n\
    #PBS -l jobfs=2GB\n\
    #PBS -l ncpus=1\n\
    #PBS -l wd\n\
    module use /g/data/v10/public/modules/modulefiles\n\
    module load dea/20191127\n\
    module load otps\n\
    python3 /g/data/r78/rt1527/dea-notebooks/MAHTS/deacoastlines_generation.py $study_area $output_name"

    echo -e ${PBS} | qsub || echo "${study_area} failed" >> log.txt
    sleep 0.2
    echo "Submitting study area $study_area $output_name"

done

