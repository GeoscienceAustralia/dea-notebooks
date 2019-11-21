#!/bin/bash

PBS="#!/bin/bash\n\
#PBS -N MAHTS\n\
#PBS -o PBS_output.out\n\
#PBS -e PBS_output.err\n\
#PBS -P r78\n\
#PBS -lstorage gdata/r78+gdata/rs0+gdata/u46+gdata/v10+gdata/wx7+gdata/xu18\n\
#PBS -q express\n\
#PBS -l walltime=24:00:00\n\
#PBS -l mem=64GB\n\
#PBS -l jobfs=2GB\n\
#PBS -l ncpus=1\n\
#PBS -l wd\n\
module use /g/data/v10/public/modules/modulefiles\n\
module load dea/20191105\n\
module load otps\n\
python /g/data/r78/rt1527/dea-notebooks/MAHTS/gadi_test.py"

echo -e ${PBS} | qsub
echo "Submitting job"
