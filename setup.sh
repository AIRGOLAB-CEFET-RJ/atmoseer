#!/bin/bash

# conda environment
conda env create -f config/environment.yml

mkdir -p ./data
mkdir -p ./data/gauge
mkdir -p ./data/sounding
mkdir -p ./data/NWP
mkdir -p ./data/NWP/ERA5
mkdir -p ./data/datasets

# docker image
#TODO docker build -t atmoseer .