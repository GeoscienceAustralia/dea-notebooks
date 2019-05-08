
#!/bin/bash
#PBS -P r78
#PBS -l walltime=12:00:00
#PBS -l mem=256GB
#PBS -l ncpus=8
#PBS -q expressbw
#PBS -m abe
#PBS -M chad.burton@ga.gov.au

cd /g/data/r78/cb3058/dea-notebooks/ICE_project/
module use /g/data/v10/public/modules/modulefiles/
module load dea

module load parallel

parallel --delay 10 -a renmark_maxNDVItiffFiles.txt python3 workaround_IE_parallel_renmark.py
wait;

# python irrigatedExtent_NMDB_parallel.py > irrigatedExtent_NMDB_parallel.log

#parallel python irrigatedExtent_NMDB_parallel.py ::: maxNDVItiffFiles.txt
#wait;

