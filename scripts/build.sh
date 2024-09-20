#!/bin/bash -c
cd /usr/app/
cp -r /src/* .
cp config/biocypher_docker_config.yaml config/biocypher_config.yaml
poetry install
python3 scripts/target_disease_script.py
chmod -R 777 biocypher-log