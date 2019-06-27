#!/bin/bash

PBS="#!/bin/bash\n\
#PBS -N animated_timeseries\n\
#PBS -o PBS_output/animations.out\n\
#PBS -e PBS_output/animations.err\n\
#PBS -P r78\n\
#PBS -q express\n\
#PBS -l walltime=1:00:00\n\
#PBS -l mem=128GB\n\
#PBS -l jobfs=2GB\n\
#PBS -l ncpus=1\n\
#PBS -l wd\n\
module use /g/data/v10/public/modules/modulefiles\n\
module load dea/20190329\n\
module load ffmpeg\n\
python /g/data/r78/rt1527/dea-notebooks/Animations/animated_timeseries.py"

echo -e ${PBS} | qsub
echo "Submitting data"
