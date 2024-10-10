#!/bin/bash -c
# Install SSL certificates
apt-get update && apt-get install -y --reinstall ca-certificates && update-ca-certificates

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

pip install --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host files.pythonhosted.org --trusted-host raw.githubusercontent.com certifi poetry-core typing-extensions urllib3 sortedcontainers six pytz idna annotated_types charset_normalizer pydantic_core biocypher poetry_core bioregistry networkx py4j pyspark tornado snakeviz typing-extensions biocypher biolink https://github.com/biolink/biolink-model/raw/v3.2.1/biolink-model.owl.ttl 
#SSL_CERT_FILE=$(python -m certifi)

cd /usr/app/
cp -r /src/* .
cp config/biocypher_docker_config.yaml config/biocypher_config.yaml
export CURL_CA_BUNDLE=""
export POETRY_HTTP_CA_CERT="/dev/null"
poetry install
pip install .
python3 scripts/target_disease_script.py
chmod -R 777 biocypher-log