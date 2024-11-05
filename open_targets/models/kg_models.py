
from enum import Enum

# Datasets
class TargetDiseaseDataset(Enum):
    """
    Enum of all the datasets used in the target-disease evidence pipeline.
    Values are the spellings used in the Open Targets parquet files.
    """

    # TODO: Where does this info come from?
    CANCER_BIOMARKERS = "cancer_biomarkers"
    CANCER_GENE_CENSUS = "cancer_gene_census"
    CHEMBL = "chembl"
    CLINGEN = "clingen"
    CRISPR = "crispr"
    EUROPE_PMC = "europepmc"
    EVA = "eva"
    EVA_SOMATIC = "eva_somatic"
    EXPRESSION_ATLAS = "expression_atlas"
    GENOMICS_ENGLAND = "genomics_england"
    GENE_BURDEN = "gene_burden"
    GENE2PHENOTYPE = "gene2phenotype"
    IMPC = "impc"
    INTOGEN = "intogen"
    ORPHANET = "orphanet"
    OT_GENETICS_PORTAL = "ot_genetics_portal"
    PROGENY = "progeny"
    REACTOME = "reactome"
    SLAP_ENRICH = "slapenrich"
    SYSBIO = "sysbio"
    UNIPROT_VARIANTS = "uniprot_variants"
    UNIPROT_LITERATURE = "uniprot_literature"

# Nodes
class TargetNodeField(Enum):
    """
    Enum of all the fields in the target dataset. Values are the spellings used
    in the Open Targets parquet files.
    """

    # mandatory fields
    TARGET_GENE_ENSG = "id"
    _PRIMARY_ID = TARGET_GENE_ENSG

    # optional fields
    TARGET_GENE_SYMBOL = "approvedSymbol"
    TARGET_GENE_BIOTYPE = "biotype"
    TARGET_TRANSCRIPT_IDS = "transcriptIds"
    TARGET_CANONICAL_TRANSCRIPT = "canonicalTranscript"
    TARGET_CANONICAL_EXONS = "canonicalExons"
    TARGET_GENOMIC_LOCATIONS = "genomicLocation"
    TARGET_ALTERNATIVE_GENES = "alternativeGenes"
    TARGET_APPROVED_NAME = "approvedName"
    TARGET_GENE_ONTOLOGY_ANNOTATIONS = "go"
    TARGET_HALLMARKS = "hallmarks"
    TARGET_ALL_SYNONYMS = "synonyms"
    TARGET_GENE_SYMBOL_SYNONYMS = "symbolSynonyms"
    TARGET_NAME_SYNONYMS = "nameSynonyms"
    TARGET_FUNCTIONAL_DESCRIPTIONS = "functionDescriptions"
    TARGET_SUBCELLULAR_LOCATIONS = "subcellularLocations"
    TARGET_CLASS = "targetClass"
    TARGET_OBSOLETE_GENE_SYMBOLS = "obsoleteSymbols"
    TARGET_OBSOLETE_GENE_NAMES = "obsoleteNames"
    TARGET_CONSTRAINT = "constraint"
    TARGET_TEP = "tep"
    TARGET_PROTEIN_IDS = "proteinIds"
    TARGET_DATABASE_XREFS = "dbXrefs"
    TARGET_CHEMICAL_PROBES = "chemicalProbes"
    TARGET_HOMOLOGUES = "homologues"
    TARGET_TRACTABILITY = "tractability"
    TARGET_SAFETY_LIABILITIES = "safetyLiabilities"
    TARGET_PATHWAYS = "pathways"


class DiseaseNodeField(Enum):
    """
    Enum of all the fields in the disease dataset. Values are the spellings used
    in the Open Targets parquet files.
    """

    # mandatory fields
    DISEASE_ACCESSION = "id"
    _PRIMARY_ID = DISEASE_ACCESSION

    # optional fields
    DISEASE_CODE = "code"
    DISEASE_DATABASE_XREFS = "dbXRefs"
    DISEASE_DESCRIPTION = "description"
    DISEASE_NAME = "name"
    DISEASE_DIRECT_LOCATION_IDS = "directLocationIds"
    DISEASE_OBSOLETE_TERMS = "obsoleteTerms"
    DISEASE_PARENTS = "parents"
    DISEASE_SKO = "sko"
    DISEASE_SYNONYMS = "synonyms"
    DISEASE_ANCESTORS = "ancestors"
    DISEASE_DESCENDANTS = "descendants"
    DISEASE_CHILDREN = "children"
    DISEASE_THERAPEUTIC_AREAS = "therapeuticAreas"
    DISEASE_INDIRECT_LOCATION_IDS = "indirectLocationIds"
    DISEASE_ONTOLOGY = "ontology"


class DrugNodeField(Enum):
    # mandatory fields
    DRUG_ACCESSION = "id"
    _PRIMARY_ID = DRUG_ACCESSION

    # optional fields
    DRUG_CANONICAL_SMILES = "canonicalSmiles"
    DRUG_INCHI_KEY = "inchiKey"
    DRUG_DRUG_TYPE = "drugType"
    DRUG_BLACK_BOX_WARNING = "blackBoxWarning"
    DRUG_NAME = "name"
    DRUG_YEAR_OF_FIRST_APPROVAL = "yearOfFirstApproval"
    DRUG_MAX_PHASE = "maximumClinicalTrialPhase"
    DRUG_PARENT_ID = "parentId"
    DRUG_HAS_BEEN_WITHDRAWN = "hasBeenWithdrawn"
    DRUG_IS_APPROVED = "isApproved"
    DRUG_TRADE_NAMES = "tradeNames"
    DRUG_SYNONYMS = "synonyms"
    DRUG_CHEMBL_IDS = "crossReferences"
    DRUG_CHILD_CHEMBL_IDS = "childChemblIds"
    DRUG_LINKED_DISEASES = "linkedDiseases"
    DRUG_LINKED_TARGETS = "linkedTargets"
    DRUG_DESCRIPTION = "description"


class GeneOntologyNodeField(Enum):
    """
    Enum of all the fields in the gene ontology dataset. Values are the
    spellings used in the Open Targets parquet files.
    """

    # mandatory fields
    GENE_ONTOLOGY_ACCESSION = "id"
    _PRIMARY_ID = GENE_ONTOLOGY_ACCESSION

    # optional fields
    GENE_ONTOLOGY_NAME = "name"

class MousePhenotypeNodeField(Enum):
    """
    Enum of all the fields in the mouse phenotype dataset. Values are the
    spellings used in the Open Targets parquet files.
    """

    # mandatory fields
    MOUSE_PHENOTYPE_ACCESSION = "modelPhenotypeId"
    _PRIMARY_ID = MOUSE_PHENOTYPE_ACCESSION

    # optional fields
    MOUSE_PHENOTYPE_LABEL = "modelPhenotypeLabel"

class MouseTargetNodeField(Enum):
    """
    Enum of all the fields in the mouse phenotype dataset related to murine
    targets of each biological model. Values are the spellings used in the Open
    Targets parquet files.
    """

    # mandatory fields
    MOUSE_TARGET_ENSG = "targetInModelEnsemblId"
    _PRIMARY_ID = MOUSE_TARGET_ENSG

    # alternative ids
    MOUSE_TARGET_SYMBOL = "targetInModel"
    MOUSE_TARGET_MGI = "targetInModelMgiId"

    # human target ensembl id
    HUMAN_TARGET_ENGS = "targetFromSourceId"


class MouseModelNodeField(Enum):
    """
    Enum of all the fields in the mouse phenotype dataset related to the mouse
    model. Values are the spellings used in the Open Targets parquet files.
    """

    # mandatory fields
    MOUSE_PHENOTYPE_MODELS = "biologicalModels"
    _PRIMARY_ID = MOUSE_PHENOTYPE_MODELS

    MOUSE_PHENOTYPE_CLASSES = "modelPhenotypeClasses"

# Edges


class TargetDiseaseEdgeField(Enum):
    """
    Enum of all the fields in the target-disease dataset. Used to generate the
    bulk of relationships in the graph. Values are the spellings used in the
    Open Targets parquet files.
    """

    # mandatory fields
    INTERACTION_ACCESSION = "id"

    TARGET_GENE_ENSG = "targetId"
    _PRIMARY_SOURCE_ID = TARGET_GENE_ENSG

    DISEASE_ACCESSION = "diseaseId"
    _PRIMARY_TARGET_ID = DISEASE_ACCESSION

    TYPE = "datatypeId"
    SOURCE = "datasourceId"
    LITERATURE = "literature"
    SCORE = "score"


class TargetGeneOntologyEdgeField(Enum):
    """
    Enum of all the fields in the target-gene ontology dataset. Used to generate the
    bulk of relationships in the graph. Values are the spellings used in the
    Open Targets parquet files.
    """

    # mandatory fields
    # INTERACTION_ACCESSION = "id"

    TARGET_GENE_ENSG = "ensemblId"
    _PRIMARY_SOURCE_ID = TARGET_GENE_ENSG

    GENE_ONTOLOGY_ACCESSION = "goId"
    _PRIMARY_TARGET_ID = GENE_ONTOLOGY_ACCESSION
    SOURCE = "goSource"
    EVIDENCE = "goEvidence"
