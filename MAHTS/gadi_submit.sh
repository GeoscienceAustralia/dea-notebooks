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

# for study_area in WA29.02 WA29.01 WA28.02 WA28.01 WA27.04 WA27.03 WA27.02 \
#                   WA27.01 WA26.04 WA26.03 WA26.02 WA26.01 WA25.01 WA24.02 \
#                   WA24.01 WA23.04

# for study_area in WA29.01 WA28.02 WA28.01 WA27.04 \
#                   WA26.04 WA26.03 WA26.02 WA26.01 WA25.01 \
#                   WA24.01 WA23.04



# for study_area in WA22.03 WA23.01 WA23.02 WA23.03 WA23.04 WA24.01 WA24.02 \
#                   WA25.01 WA26.01 WA26.02 WA26.03 WA26.04 WA27.01 WA27.02 \
#                   WA27.03 WA27.04 WA28.01 WA28.02 WA29.01 WA29.02 WA29.03 \
#                   WA30.01 WA30.02 WA31.01 WA31.02 WA31.03
                  
# for study_area in SA07.04 SA06.03 SA07.02 SA07.03 SA08.01 SA07.05 SA05.05 \
#                   SA06.02 SA05.06 SA05.04 SA06.01 SA05.07 SA05.03 SA06.06 \
#                   SA05.02 SA05.01 SA09.01 SA03.01 SA10.01 SA08.03 SA04.01 \
#                   SA03.02 SA02.01 SA04.02 SA07.01 SA04.03 SA01.02 SA01.01

# for study_area in VIC04.08 VIC04.05 VIC02.02 VIC04.02 VIC01.02 VIC05.01 VIC04.06 \
#                   VIC04.07 VIC02.03 VIC04.02 VIC04.04 VIC05.02 VIC04.03 VIC06.01 \
#                   VIC06.02 VIC03.01 VIC04.01 VIC01.01 VIC06.03 VIC06.04

# for study_area in NT03.01 NT02.05 NT04.01 NT02.03 NT02.04 NT04.04 NT04.02 \
#                   WA36.01 NT02.01 WA35.03 WA35.01 NT02.02 NT04.03 WA36.02 \
#                   WA35.04 WA35.02 WA34.03 NT01.01 WA33.02 WA33.01 WA32.01 \
#                   WA34.02 WA32.02 WA31.04 WA31.03 WA34.01 WA31.01 WA31.02 \
#                   WA32.04 WA27.03 WA27.01 WA26.03 WA27.04 WA36.03 WA29.03 \
#                   WA29.01 WA27.02 WA24.01 WA23.04 WA26.04 WA24.02 WA23.03 \
#                   WA23.02 WA28.02 WA26.02 NT01.02 WA25.01 WA32.03 WA26.01 \
#                   WA30.01 WA28.01 WA30.02 WA29.02

for study_area in 1677
                  
do

    PBS="#!/bin/bash\n\
    #PBS -N ${study_area}\n\
    #PBS -o MAHTS_${study_area}.out\n\
    #PBS -e MAHTS_${study_area}.err\n\
    #PBS -l storage=gdata/v10+gdata/r78+gdata/xu18+gdata/fk4\n\
    #PBS -P r78\n\
    #PBS -q express\n\
    #PBS -l walltime=24:00:00\n\
    #PBS -l mem=128GB\n\
    #PBS -l jobfs=2GB\n\
    #PBS -l ncpus=1\n\
    #PBS -l wd\n\
    module use /g/data/v10/public/modules/modulefiles\n\
    module load dea/20191127\n\
    module load otps\n\
    python3 /g/data/r78/rt1527/dea-notebooks/MAHTS/MAHTS_generation.py $study_area"

    echo -e ${PBS} | qsub || echo "${study_area} failed" >> log.txt
    sleep 0.2
    echo "Submitting study area $study_area"

done


#     source /etc/bashrc\n\
#     export PYTHONPATH=/home/561/rt1527/.local/lib/python3.6/site-packages/:$PYTHONPATH\n\

#     python3 /g/data/r78/rt1527/dea-notebooks/MAHTS/MAHTS_generation.py $study_area\n\ 
#     python3 /g/data/r78/rt1527/dea-notebooks/MAHTS/MAHTS_stats.py $study_area"