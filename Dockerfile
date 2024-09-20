FROM andimajore/biocyper_base:python3.10 as setup-stage

WORKDIR /usr/app/
COPY pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install
COPY . ./

# Install Java
RUN apt-get update && \
    apt-get install -y default-jdk && \
    rm -rf /var/lib/apt/lists/*

# Find the Java installation path
RUN export JAVA_HOME=$(dirname $(dirname $(update-alternatives --list java))) && \
    echo "JAVA_HOME is set to $JAVA_HOME"

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

RUN python3 scripts/target_disease_script.py

FROM neo4j:4.4-enterprise as deploy-stage
COPY --from=setup-stage /usr/app/biocypher-out/ /var/lib/neo4j/import/
COPY docker/* ./
RUN cat biocypher_entrypoint_patch.sh | cat - /startup/docker-entrypoint.sh > docker-entrypoint.sh && mv docker-entrypoint.sh /startup/ && chmod +x /startup/docker-entrypoint.sh
