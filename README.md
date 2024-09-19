# Open Targets BioCypher KG

This is a collection of [BioCypher](https://biocypher.org) adapters and
corresponding scripts for Open Targets platform data. It is a work in progress.

## Installation

The project uses [Poetry](https://python-poetry.org). You can install it like
this:

```
git clone https://github.com/biocypher/open-targets.git
cd open-targets
poetry install
```

Poetry will create a virtual environment according to your configuration (either
centrally or in the project folder). You can activate it by running `poetry
shell` inside the project directory. Alternatively, you can use a different
package manager to install the dependencies listed in `pyproject.toml`.

### Note about pycurl

You may encounter an error in executing the script combining this adapter and
the UniProt adapter about the SSL backend in pycurl: `ImportError: pycurl:
libcurl link-time ssl backend (openssl) is different from compile-time ssl
backend (none/other)`

Should this happen, it can be fixed as described here:
https://stackoverflow.com/questions/68167426/how-to-install-a-package-with-poetry-that-requires-cli-args
by running `poetry shell` followed by `pip list`, noting the version of pycurl,
and then running `pip install --compile --install-option="--with-openssl"
--upgrade --force-reinstall pycurl==<version>` to provide the correct SSL
backend.

## Open Targets target-disease associations

Target-disease association evidence is available from the Open Targets website
at https://platform.opentargets.org/downloads. The data can be downloaded in
Parquet format, which is a columnar data format that is compatible with Spark
and other big data tools. Currently, the data have to be manually downloaded
(e.g. using the wget command supplied on the website) and placed in the
`data/ot_files` directory. The adapter currently supports version 23.02 of the
data. Available datasets: `Target`, `Disease/Phenotype`, `Drug`, `Target - gene
ontology`, `Target - mouse phenotypes` and `Target - Disease Evidence`. CAVE:
The latter, which is the main source of target-disease interactions in the open
targets platform, is provided in two links, one for the literature evidence
(`literature/evidence`) and one for the full aggregated set (simply `evidence`).
The adapter uses the full set, so make sure to download the correct one. The
scripts directory contains a `parquet_download.sh` script that can be used to
download the files (make sure to execute it in the correct folder,
`data/ot_files`).

To transfer the columnar data to a knowledge graph, we use the adapter in
`otar_biocypher/target_disease_evidence_adapter.py`, which is called from the script
`scripts/target_disease_script.py`. This script produces a set of
BioCypher-compatible files in the `biocypher-out` directory. To create the
knowledge graph from these files, you can find a version of the neo4j-admin
import command for the processed data in each individual output folder, under
the file name `neo4j-admin-import-call.sh`, which simply needs to be executed in
the home directory of the target database. More information about the BioCypher
package can be found at https://biocypher.org.

Please note that, by default, the adapter will be in `test mode`, which means
that it will only process a small subset of the data. To process the full data,
you can set the `test_mode` parameter in the adapter to `False` (or remove it).

### Adapter combination: UniProt and Dependency Map

To demonstrate the combination of multiple adapters to yield a single harmonised
knowledge graph, we add the [UniProt
adapter](https://github.com/HUBioDataLab/CROssBAR-BioCypher-Migration) (created
in the context of the CROssBAR v2 project) and the [Dependency Map
adapter](https://github.com/saezlab/DepMap-BioCypher) to the target-disease
knowledge graph creation script. The resulting script is
`scripts/target_disease_script_extended.py`.

Please note that while the UniProt adapter downloads data directly from UniProt
through pypath, the Dependency Map adapter is only functional for demonstration
purposes, as it requires the availability of local data (which is limited to
100 entries for our demo case).

## 🐳 Docker

This repo also contains a `docker compose` workflow to create the example
database using BioCypher and load it into a dockerised Neo4j instance
automatically. To run it, simply execute `docker compose up -d` in the root 
directory of the project. This will start up a single (detached) docker
container with a Neo4j instance that contains the knowledge graph built by
BioCypher as the DB `neo4j` (the default DB), which you can connect to and
browse at localhost:7474. Authentication is deactivated by default and can be
modified in the `docker_variables.env` file (in which case you need to provide
the .env file to the deploy stage of the `docker-compose.yml`).

Regarding the BioCypher build procedure, the `biocypher_docker_config.yaml` file
is used instead of the `biocypher_config.yaml` (configured in
`scripts/build.sh`). Everything else is the same as in the local setup. The
first container (`build`) installs and runs the BioCypher pipeline, the second
container (`import`) installs Neo4j and runs the import, and the third container
(`deploy`) deploys the Neo4j instance on localhost. The files are shared using a
Docker Volume. This three-stage setup strictly is not necessary for the mounting
of a read-write instance of Neo4j, but is required if the purpose is to provide
a read-only instance (e.g. for a web app) that is updated regularly; for an
example, see the [meta graph
repository](https://github.com/biocypher/meta-graph). The read-only setting is
configured in the `docker-compose.yml` file
(`NEO4J_dbms_databases_default__to__read__only: "false"`) and is deactivated by
default.