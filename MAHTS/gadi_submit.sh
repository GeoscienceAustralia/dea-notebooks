#!/bin/bash

# Sydney
# for study_area in NSW06.05 NSW06.04 NSW06.02 NSW06.03

# Cabarita
# for study_area in QLD15.03 QLD16.01 QLD16.02 QLD16.04 QLD16.05 QLD16.06 \
#                   QLD17.01 QLD18.01 QLD17.02 QLD18.02 NSW01.01 NSW01.02 \
#                   NSW01.03 NSW01.04 NSW02.01

# Other QLD
# for study_area in QLD09.04 QLD12.04 QLD12.03

# # Pilbara
# for study_area in WA29.02 WA29.01 WA28.02 WA28.01 WA27.04 WA27.03 WA27.02 \
#                   WA27.01 WA26.04 WA26.03 WA26.02 WA26.01 WA25.01 WA24.02 \
#                   WA24.01 WA23.04

# # Perth
# for study_area in WA13.03 WA13.01 WA12.02

# # High memory
# for study_area in QLD16.02 
# for study_area in WA26.04 

for study_area in WA29.02

do

    PBS="#!/bin/bash\n\
    #PBS -N ${study_area}\n\
    #PBS -o MAHTS_${study_area}.out\n\
    #PBS -e MAHTS_${study_area}.err\n\
    #PBS -P r78\n\
    #PBS -q express\n\
    #PBS -l walltime=6:00:00\n\
    #PBS -l mem=32GB\n\
    #PBS -l jobfs=2GB\n\
    #PBS -l ncpus=1\n\
    #PBS -l wd\n\
    module use /g/data/v10/public/modules/modulefiles\n\
    module load dea/20191105\n\
    module load otps\n\
    python /g/data/r78/rt1527/dea-notebooks/MAHTS/MAHTS_stats.py $study_area"

    echo -e ${PBS} | qsub
    sleep 0.2
    echo "Submitting study area $study_area"

done


#     source /etc/bashrc\n\
#     export PYTHONPATH=/home/561/rt1527/.local/lib/python3.6/site-packages/:$PYTHONPATH\n\