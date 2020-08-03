#!usr/bin/env bash

#code written by Bex D on 03.09.2018

module use /g/data/v10/public/modules/modulefiles/

module load dea/20180515

module load otps

cd /g/data/r78/rjd547/jupyter_notebooks/dea-notebooks/

jupyter notebook &

#module use  /g/data/r78/rjd547/modules/

#module load bex-py/1.5.1

#jupyter notebook --NotebookApp.iopub_data_rate_limit=10000000000

#to run this code, type source <filename.sh>

