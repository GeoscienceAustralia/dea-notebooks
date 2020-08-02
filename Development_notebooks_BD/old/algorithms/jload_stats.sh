#!/usr/bin/env bash

#code written by Bex D on 30.10.2017

module use /g/data/v10/public/modules/modulefiles/

module load agdc-py3-prod/1.5.4

module load agdc_statistics/0.9a8

module load dea-prod

#module use  /g/data/r78/rjd547/modules/

#module load bex-py/1.5.1

jupyter notebook --NotebookApp.iopub_data_rate_limit=10000000000

#to run this code, type source <filename.sh>

