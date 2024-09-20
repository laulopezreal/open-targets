#!/bin/bash -c

# Install Java
apt-get update && \
    apt-get install -y default-jdk && \
    rm -rf /var/lib/apt/lists/*

# Find the Java installation path
export JAVA_HOME=$(dirname $(dirname $(update-alternatives --list java))) && \
    echo "JAVA_HOME is set to $JAVA_HOME"

# Set JAVA_HOME environment variable
# JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
PATH="$JAVA_HOME/bin:$PATH"

cd /usr/app/
cp -r /src/* .
cp config/biocypher_docker_config.yaml config/biocypher_config.yaml
poetry install
python3 scripts/target_disease_script.py
chmod -R 777 biocypher-log