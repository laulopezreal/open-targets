from typing import Optional
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession, DataFrame, functions as F
from bioregistry.resolve import normalize_curie
from biocypher._logger import logger
from tqdm import tqdm
import functools
import base64

from open_targets.models.kg_models import (
    TargetDiseaseDataset,
    TargetNodeField,
    DiseaseNodeField,
    DrugNodeField,
    GeneOntologyNodeField,
    MousePhenotypeNodeField,
    MouseTargetNodeField,
    MouseModelNodeField,
    TargetDiseaseEdgeField,
    TargetGeneOntologyEdgeField,
)

_licences = {
    "cancer_biomarkers": "NA",  # TODO
    "cancer_gene_census": "Commercial use for Open Targets",
    "chembl": "CC BY-SA 3.0",
    "clingen": "CC0 1.0",
    "crispr": "NA",  # TODO
    "europepmc": "CC BY-NC 4.0",  # can be open access, CC0, CC BY, or CC BY-NC
    "eva": "EMBL-EBI terms of use",
    "eva_somatic": "EMBL-EBI terms of use",
    "expression_atlas": "CC BY 4.0",
    "genomics_england": "Commercial use for Open Targets",
    "gene_burden": "NA",  # TODO
    "gene2phenotype": "EMBL-EBI terms of use",
    "impc": "NA",  # TODO
    "intogen": "CC0 1.0",
    "orphanet": "CC BY 4.0",
    "ot_genetics_portal": "EMBL-EBI terms of use",
    "progeny": "Apache 2.0",
    "reactome": "CC BY 4.0",
    "slapenrich": "MIT",
    "sysbio": "NA",  # TODO
    "uniprot_variants": "CC BY 4.0",
    "uniprot_literature": "CC BY 4.0",
}

spark_conf = (
    SparkConf()
    .setAppName("otar_biocypher")
    .setMaster("local")
    .set("spark.driver.memory", "8g")
    .set("spark.executor.memory", "8g")
)

spark_optim_conf = (
    SparkConf()
    .setAppName("otar_biocypher")
    .setMaster("local")
    .set("spark.executor.memory", "32g")
    .set("spark.driver.memory", "32g")
    .set("spark.executor.cores", "8")
    # .set("spark.sql.shuffle.partitions", "2000")
    # .set("spark.default.parallelism", "2000")
    .set("spark.memory.fraction", "0.8")
    .set("spark.memory.storageFraction", "0.3")
    .set(
        "spark.executor.extraJavaOptions",
        "-XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=35 -XX:MaxGCPauseMillis=200",
    )
    .set(
        "spark.driver.extraJavaOptions",
        "-XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=35 -XX:MaxGCPauseMillis=200",
    )
)


class TargetDiseaseEvidenceAdapter:
    def __init__(
        self,
        datasets: list[TargetDiseaseDataset],
        node_fields: list[
            TargetNodeField
            | DiseaseNodeField
            | DrugNodeField
            | GeneOntologyNodeField
            | MousePhenotypeNodeField
            | MouseTargetNodeField
            | MouseModelNodeField
        ],
        target_disease_edge_fields: list[TargetDiseaseEdgeField],
        target_go_edge_fields: list[TargetGeneOntologyEdgeField],
        test_mode: bool = False,
        spark_config: SparkConf = spark_optim_conf,
    ):
        self.datasets = datasets
        self.node_fields = node_fields
        self.target_disease_edge_fields = target_disease_edge_fields
        self.target_go_edge_fields = target_go_edge_fields
        self.test_mode = test_mode
        self.current_batches = list()

        if not self.datasets:
            raise ValueError("datasets must be provided")

        if not self.node_fields:
            raise ValueError("node_fields must be provided")

        if not self.target_disease_edge_fields:
            raise ValueError("target_disease_edge_fields must be provided")

        if not self.target_go_edge_fields:
            raise ValueError("target_go_edge_fields must be provided")

        if TargetNodeField.TARGET_GENE_ENSG not in self.node_fields:
            raise ValueError("TargetNodeField.TARGET_GENE_ENSG must be provided")

        if DiseaseNodeField.DISEASE_ACCESSION not in self.node_fields:
            raise ValueError("DiseaseNodeField.DISEASE_ACCESSION must be provided")

        if GeneOntologyNodeField.GENE_ONTOLOGY_ACCESSION not in self.node_fields:
            raise ValueError(
                "GeneOntologyNodeField.GENE_ONTOLOGY_ACCESSION must be provided"
            )

        if self.test_mode:
            logger.warning(
                "Open Targets adapter: Test mode is enabled. "
                "Only processing 100 rows."
            )

        logger.info("Creating Spark session.")
        # Set up Spark context
        self.sc = SparkContext(conf=spark_config)

        # Create SparkSession
        self.spark = SparkSession.builder.master("local").appName("otar_biocypher").getOrCreate()  # type: ignore

    def download_data(self, version: str, force: bool = False):
        """
        Download datasets from Open Targets website. Manage downloading and
        caching of files. TODO

        Args:

            version: Version of the Open Targets data to download.

            force: Whether to force download of files even if they already
            exist.
        """
        pass

    def load_data(
        self,
        stats: bool = False,
        show_nodes: bool = False,
        show_edges: bool = False,
    ):
        """
        Load data from disk into Spark DataFrames.

        Args:

            stats: Whether to print out schema and counts of nodes and edges.

            show_nodes: Whether to print out the first row of each node
            dataframe.

            show_edges: Whether to print out the first row of each edge
            dataframe.
        """

        logger.info("Loading Open Targets data from disk.")

        # Read in evidence data and target / disease annotations
        evidence_path = "data/ot_files/evidence"
        self.evidence_df = self.spark.read.parquet(evidence_path)

        target_path = "data/ot_files/targets"
        self.target_df = self.spark.read.parquet(target_path)

        disease_path = "data/ot_files/diseases"
        self.disease_df = self.spark.read.parquet(disease_path)

        drug_path = "data/ot_files/molecule"
        self.drug_df = self.spark.read.parquet(drug_path)

        go_path = "data/ot_files/go"
        self.go_df = self.spark.read.parquet(go_path)

        mp_path = "data/ot_files/mousePhenotypes"
        self.mp_df = self.spark.read.parquet(mp_path)

        if stats:
            # print schema
            print(self.evidence_df.printSchema())
            print(self.target_df.printSchema())
            print(self.disease_df.printSchema())
            print(self.drug_df.printSchema())
            print(self.go_df.printSchema())
            print(self.mp_df.printSchema())

            # print number of rows
            print(f"Length of evidence data: {self.evidence_df.count()} entries")
            print(f"Length of target data: {self.target_df.count()} entries")
            print(f"Length of disease data: {self.disease_df.count()} entries")
            print(f"Length of drug data: {self.drug_df.count()} entries")
            print(f"Length of GO data: {self.go_df.count()} entries")
            print(f"Length of Mouse Phenotype data: {self.mp_df.count()} entries")

            # print number of rows per datasource
            self.evidence_df.groupBy("datasourceId").count().show(100)

        if show_edges:
            for dataset in [field.value for field in self.datasets]:
                self.evidence_df.where(self.evidence_df.datasourceId == dataset).show(
                    1, 50, True
                )

        if show_nodes:
            self.target_df.show(1, 50, True)
            self.disease_df.show(1, 50, True)
            self.drug_df.show(1, 50, True)
            self.go_df.show(1, 50, True)
            self.mp_df.show(1, 50, True)

    def show_datasources(self):
        """
        Utility function to get all datasources in the evidence data.
        """

        # collect all distinct datasourceId values
        datasources = self.evidence_df.select("datasourceId").distinct().collect()

        # convert to list
        self.datasources = [x.datasourceId for x in datasources]
        print(self.datasources)

    def _yield_node_type(
        self,
        df: DataFrame,
        node_field_type,
        ontology_class: Optional[str] = None,
    ):
        """
        Yield the node type from the dataframe.

        Args:

            df: Spark DataFrame containing the node data.

            node_field_type: Enum containing the node fields.

            ontology_class: Ontological class of the node (corresponding to the
            `label_in_input` field in the schema configuration).
        """

        # Select columns of interest
        df = df.select(
            [field.value for field in self.node_fields if isinstance(field, node_field_type)]  # type: ignore
        )

        logger.info(f"Generating nodes of {node_field_type}.")

        if self.test_mode:
            df = df.limit(100)

        for row in tqdm(df.collect()):
            # normalize id
            _id, _type = _process_id_and_type(
                row[node_field_type._PRIMARY_ID.value], ontology_class
            )

            # switch mouse gene type
            if node_field_type == MouseTargetNodeField:
                _type = "mouse gene"

            if not _id:
                logger.debug(f"Node <{node_field_type}> has no id. Skipping.")
                continue

            logger.debug(f"Processed {node_field_type} with id {_id} and type {_type}")

            _props = {}
            _props["version"] = "22.11"
            _props["source"] = "Open Targets"
            _props["licence"] = "https://platform-docs.opentargets.org/licence"

            for field in self.node_fields:
                if not isinstance(field, node_field_type):
                    continue

                if row[field.value]:
                    _props[field.value] = row[field.value]

            yield (_id, _type, _props)

    def get_nodes(self):
        """
        Yield nodes from the target and disease dataframes.
        """

        # Targets
        yield from self._yield_node_type(self.target_df, TargetNodeField, "ensembl")

        # Diseases
        yield from self._yield_node_type(self.disease_df, DiseaseNodeField)

        # Drugs
        yield from self._yield_node_type(self.drug_df, DrugNodeField, "chembl")

        # Gene Ontology
        yield from self._yield_node_type(self.go_df, GeneOntologyNodeField)

        # Mouse Phenotypes
        only_mp_df = self.mp_df.select(
            [field.value for field in MousePhenotypeNodeField]
        ).dropDuplicates()
        yield from self._yield_node_type(only_mp_df, MousePhenotypeNodeField)

        # Mouse Targets
        mouse_target_df = self.mp_df.select(
            [field.value for field in MouseTargetNodeField]
        ).dropDuplicates()
        yield from self._yield_node_type(
            mouse_target_df, MouseTargetNodeField, "ensembl"
        )

    def get_edge_batches(self, df: DataFrame) -> DataFrame:
        """
        Adds partition number to the evidence dataframe and returns the data
        frame.

        Args:

            df: The evidence dataframe.

        Returns:

            The evidence dataframe with a new column "partition_num" containing
            the partition number.
        """

        logger.info("Generating batches.")

        # add partition number to self.evidence_df as column
        df = df.withColumn("partition_num", F.spark_partition_id())
        df.persist()

        self.current_batches = [
            int(row.partition_num)
            for row in df.select("partition_num").distinct().collect()
        ]

        logger.info(f"Generated {len(self.current_batches)} batches.")

        return df

    def get_gene_go_edges(self, batch_number: int):
        """
        Yield edges from the evidence dataframe per batch.
        """

        # Check if self.evidence_df has column partition_num
        if "partition_num" not in self.target_df.columns:
            raise ValueError(
                "df does not have column partition_num. "
                "Please run get_edge_batches() first."
            )

        logger.info("Generating Gene -> GO edges.")

        logger.info(
            f"Processing batch {batch_number+1} of {len(self.current_batches)}."
        )

        yield from self._process_gene_go_edges(
            self.target_df.where(self.target_df.partition_num == batch_number)
        )

    def _process_gene_go_edges(self, batch: DataFrame):
        """
        Process one batch of Gene -> GO edges.

        Args:
            batch: Spark DataFrame containing the edges of one batch.
        """
        logger.info(f"Batch size: {batch.count()} edges.")

        if self.test_mode:
            # limit batch df to 100 rows
            batch = batch.limit(100)

        go_exploded_df = batch.withColumn("go_exploded", F.explode("go")).drop("go")
        batch = go_exploded_df.withColumn("goId", F.col("go_exploded.id"))
        batch = batch.withColumn("goSource", F.col("go_exploded.source"))
        batch = batch.withColumn("goEvidence", F.col("go_exploded.evidence"))
        batch = batch.withColumn("goEcoId", F.col("go_exploded.ecoId"))
        batch = batch.withColumn("goAspect", F.col("go_exploded.aspect"))
        batch = batch.withColumn("goGeneProduct", F.col("go_exploded.geneProduct"))

        batch = batch.withColumnRenamed("id", "ensemblId")

        rows = batch.collect()
        # yield edges per row of edge_df, skipping null values
        for row in tqdm(rows):
            # collect properties from fields, skipping null values
            properties = {}
            for field in self.target_go_edge_fields:
                if field == TargetGeneOntologyEdgeField.SOURCE:
                    field_value = field.value
                    properties["source"] = row[field_value]
                if field == TargetGeneOntologyEdgeField.EVIDENCE:
                    field_value = field.value
                    properties["evidence"] = row[field_value]

                properties[field.value] = row[field.value]

            properties["version"] = "22.11"
            properties["licence"] = "my_licence"

            go_id, _ = _process_id_and_type(row.goId, "go")
            gene_id, _ = _process_id_and_type(row.ensemblId, "ensembl")
            hash_value = hash((gene_id, go_id, frozenset(sorted(properties.items()))))
            id = base64.b64encode(str(hash_value).encode()).decode('utf-8')

            yield (
                id,
                gene_id,
                go_id,
                "GENE_TO_GO_TERM_ASSOCIATION",
                properties,
            )

    def get_gene_disease_edges(self, batch_number: int):
        """
        Yield edges from the evidence dataframe per batch.

        Args:
            batch_number: The number of the current batch.
        """

        # Check if self.evidence_df has column partition_num
        if "partition_num" not in self.evidence_df.columns:
            raise ValueError(
                "df does not have column partition_num. "
                "Please run get_edge_batches() first."
            )

        logger.info("Generating edges.")

        logger.info(
            f"Processing batch {batch_number+1} of {len(self.current_batches)}."
        )

        yield from self._process_gene_disease_edges(
            self.evidence_df.where(self.evidence_df.partition_num == batch_number)
        )

    def _process_gene_disease_edges(self, batch):
        """
        Process one batch of edges.

        Args:

            batch: Spark DataFrame containing the edges of one batch.
        """

        logger.info(f"Batch size: {batch.count()} edges.")

        if self.test_mode:
            # limit batch df to 100 rows
            batch = batch.limit(100)

        # yield edges per row of edge_df, skipping null values
        for row in tqdm(batch.collect()):
            # collect properties from fields, skipping null values
            properties = {}
            for field in self.target_disease_edge_fields:
                # skip disease and target ids, relationship id, and datatype id
                # as they are encoded in the relationship
                if field not in [
                    TargetDiseaseEdgeField.LITERATURE,
                    TargetDiseaseEdgeField.SCORE,
                    TargetDiseaseEdgeField.SOURCE,
                ]:
                    continue

                if field == TargetDiseaseEdgeField.SOURCE:
                    properties["source"] = row[field.value]
                    properties["licence"] = _find_licence(row[field.value])
                elif row[field.value]:
                    properties[field.value] = row[field.value]

            properties["version"] = "22.11"

            disease_id, _ = _process_id_and_type(row.diseaseId)
            gene_id, _ = _process_id_and_type(row.targetId, "ensembl")

            yield (
                row.id,
                gene_id,
                disease_id,
                row.datatypeId,
                properties,
            )


@functools.lru_cache()
def _process_id_and_type(inputId: str, _type: Optional[str] = None):
    """
    Process diseaseId and diseaseType fields from evidence data. Process
    gene (ENSG) ids.

    Args:

        inputId: id of the node.

        _type: type of the node.
    """

    if not inputId:
        return (None, None)

    _id = None

    if _type:
        _id = normalize_curie(f"{_type}:{inputId}")

        return (_id, _type)

    # detect delimiter (either _ or :)
    if "_" in inputId:
        _type = inputId.split("_")[0].lower()

        # special case for OTAR TODO
        if _type == "otar":
            _id = f"otar:{inputId.split('_')[1]}"
        else:
            _id = normalize_curie(inputId, sep="_")

    elif ":" in inputId:
        _type = inputId.split(":")[0].lower()
        _id = normalize_curie(inputId, sep=":")

    if not _id:
        return (None, None)

    return (_id, _type)


def _find_licence(source: str) -> str:
    """
    Find and return the licence for a source.

    Args:

        source: source of the evidence. Spelling as in the Open Targets
        evidence data.
    """
    return _licences.get(source, "Unknown")
