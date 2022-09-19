#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BioCypher - OTAR prototype
"""

import biocypher
import neo4j_utils as nu
import pandas as pd
from biocypher._logger import logger
from utils._id_type_processing import _process_node_id_and_type
from utils._transactions import (
    get_bin_int_rels_tx,
    get_interactor_to_organism_edges_tx,
    get_nodes_tx,
)

logger.debug(f"Loading module {__name__}.")


class BioCypherAdapter:
    def __init__(
        self,
        dirname=None,
        db_name="neo4j",
        id_batch_size: int = int(1e6),
        user_schema_config_path="config/schema_config.yaml",
    ):

        self.db_name = db_name
        self.id_batch_size = id_batch_size

        # write driver
        self.bcy = biocypher.Driver(
            offline=True,  # set offline to true,
            # connect to running DB for input data via the neo4j driver
            user_schema_config_path=user_schema_config_path,
            delimiter="¦",
            skip_bad_relationships=True,
        )
        # start writer
        self.bcy.start_bl_adapter()
        self.bcy.start_batch_writer(dirname=dirname, db_name=self.db_name)

        # read driver
        self.driver = nu.Driver(
            db_name="neo4j",
            db_uri="bolt://localhost:7687",
            db_passwd="your_password_here",
            multi_db=False,
            max_connection_lifetime=7200,
        )

    def write_to_csv_for_admin_import(self):
        """
        Write nodes and edges to admin import csv files.
        """

        self.write_nodes()
        self.write_edges()
        self.bcy.write_import_call()
        self.bcy.log_missing_bl_types()

    ############################## NODES ####################################

    def write_nodes(self):
        """
        Write nodes to admin import csv files.
        """

        # get node labels from csv
        with open("data/node_labels.csv", "r") as f:
            # import to pandas dataframe
            node_labels = pd.read_csv(f)

        node_labels = [
            "GraphPublication",
            "GraphOrganism",
            "GraphExperiment",
        ]

        # Single labels other than Interactors
        for label in node_labels:
            with self.driver.session() as session:
                # writing of one type needs to be completed inside
                # this session
                session.read_transaction(
                    self._get_node_ids_and_write_batches_tx, label
                )

        # Interactors
        with self.driver.session() as session:
            # also writes edges from interactors to organisms
            session.read_transaction(
                self._get_interactor_ids_and_write_batches_tx,
                "GraphInteractor",
            )

    ## regular nodes ##

    def _get_node_ids_and_write_batches_tx(
        self,
        tx,
        label,
    ):
        """
        Write nodes to admin import csv files. Writer function needs to be
        performed inside the transaction. Write edges from interactors to
        organisms.
        """

        result = tx.run(f"MATCH (n:{label}) " "RETURN id(n) as id")

        id_batch = []
        for record in result:
            # collect in batches
            id_batch.append(record["id"])
            if len(id_batch) == self.id_batch_size:

                # if full batch, trigger write process
                self._write_nodes(id_batch, label)
                id_batch = []

            # check if result depleted
            elif result.peek() is None:

                # write last batch
                self._write_nodes(id_batch, label)

    def _write_nodes(self, id_batch, label):
        """
        Write nodes to admin import csv files. Needs to be performed in a
        transaction.

        Args:

            id_batch: list of edge ids to write

            label: label of the node type
        """

        def node_gen():
            with self.driver.session() as session:
                results = session.read_transaction(get_nodes_tx, id_batch)

                for res in results:

                    # TODO source
                    _id, _type = _process_node_id_and_type(res["n"], label)
                    _props = res["n"]
                    yield (_id, _type, _props)

        self.bcy.write_nodes(
            nodes=node_gen(),
            db_name=self.db_name,
        )

    ## interactors ##

    def _get_interactor_ids_and_write_batches_tx(
        self,
        tx,
        label,
    ):
        """
        Write nodes to admin import csv files. Writer function needs to be
        performed inside the transaction.
        """

        result = tx.run(f"MATCH (n:{label}) " "RETURN id(n) as id")

        id_batch = []
        for record in result:
            # collect in batches
            id_batch.append(record["id"])
            if len(id_batch) == self.id_batch_size:

                # if full batch, trigger write process
                self._write_interactors(id_batch, label)
                id_batch = []

            # check if result depleted
            elif result.peek() is None:

                # write last batch
                self._write_interactors(id_batch, label)

    def _write_interactors(self, id_batch, label):
        """
        Write interactor nodes to admin import csv files. Also write
        interactor to organism edges. Needs to be performed in a
        transaction.

        Args:

            id_batch: list of node ids to write

            label: label of the node type
        """

        nodes = []
        edges = []

        with self.driver.session() as session:
            results = session.read_transaction(
                get_interactor_to_organism_edges_tx, id_batch
            )

            for res in results:

                typ = res["typ"]
                src = res["src"]

                (
                    _interactor_id,
                    _interactor_type,
                ) = _process_node_id_and_type(res["n"], typ or label, src)

                _interactor_props = res["n"]

                nodes.append(
                    (_interactor_id, _interactor_type, _interactor_props)
                )

                if res.get("o"):
                    _organism_id, _ = _process_node_id_and_type(
                        res["o"], "GraphOrganism"
                    )

                    _interaction_type = "INTERACTOR_TO_ORGANISM"
                    _interaction_props = {}

                    edges.append(
                        (
                            None,
                            _interactor_id,
                            _organism_id,
                            _interaction_type,
                            _interaction_props,
                        )
                    )
                else:
                    logger.debug(
                        f"No organism found for interactor {_interactor_props}"
                    )

        self.bcy.write_nodes(
            nodes=nodes,
            db_name=self.db_name,
        )

        self.bcy.write_edges(
            edges=edges,
            db_name=self.db_name,
        )

    ############################## EDGES ####################################

    def write_edges(self) -> None:
        """
        Write edges to admin import csv files.
        """

        # dedicated function for binary interactions
        with self.driver.session() as session:
            # writing of one type needs to be completed inside
            # this session
            session.read_transaction(
                self._get_binary_interaction_ids_and_write_batches_tx
            )

    def _get_binary_interaction_ids_and_write_batches_tx(self, tx):
        """
        Write edges to admin import csv files. Writer function needs to be
        performed inside the transaction.
        """

        result = tx.run(
            f"MATCH (n:GraphBinaryInteractionEvidence) "
            "RETURN id(n) as id"
            " LIMIT 10"
        )

        id_batch = []
        for record in result:
            # collect in batches
            if len(id_batch) < self.id_batch_size:
                id_batch.append(record["id"])

                # check if result depleted
                if result.peek() is None:
                    # write last batch
                    self._write_bin_int_edges(id_batch)

            # if full batch, trigger write process
            else:
                self._write_bin_int_edges(id_batch)
                id_batch = []

    def _write_bin_int_edges(self, id_batch):
        """
        Write edges to admin import csv files. Needs to be performed in a
        transaction.

        Args:

            id_batch: list of edge ids to write

        """

        # TODO: IntAct interaction IDs refer to multiple binary interactions;
        # as is, nodes connected to multiple targets will have multiple edges
        # to the same interaction node. What is the biological meaning behind
        # this? Complexes, experiments, etc.?

        def edge_gen():
            with self.driver.session() as session:
                results = session.read_transaction(
                    get_bin_int_rels_tx, id_batch
                )

                for res in results:
                    # TODO role -> relationship type

                    # extract relevant ids
                    _id = res["n"].get("ac")
                    # seems like all protein-protein interactions at
                    # least have an EBI identifier; however, these IDs
                    # are not unique to each pairwise interaction
                    if not _id:
                        logger.debug(
                            "No id found for binary interaction evidence: "
                            f"{res}"
                        )

                    ## primary interaction edge

                    # also carrying ac: efo, rcsb pdb, wwpdb
                    _src_id, _src_type = _process_node_id_and_type(
                        res["a"], res["typ_a"], res["src_a"]
                    )
                    _tar_id, _tar_type = _process_node_id_and_type(
                        res["b"], res["typ_b"], res["src_b"]
                    )

                    _source = res["source"]

                    # subtypes according to the type of association
                    # _type = "_".join(
                    #     [
                    #         res["typ_a"],
                    #         res["typ_b"],
                    #         _source,
                    #         res["nt"].get("shortName"),
                    #     ]
                    # )
                    _type = res["nt"].get("shortName")

                    # properties of BinaryInteractionEvidence
                    _props = res["n"]
                    # add interactionType properties (redundant, should
                    # later be encoded in labels)
                    _props["interactionTypeShortName"] = res["nt"].get(
                        "shortName"
                    )
                    _props["interactionTypeFullName"] = res["nt"].get(
                        "fullName"
                    )
                    _props["interactionTypeIdentifierStr"] = res["nt"].get(
                        "mIIdentifier"
                    )

                    _props["mi_score"] = res["mi_score"]

                    # pass roles of a and b: is there a smarter way to do this?
                    _props["src_role"] = res["role_a"]
                    _props["tar_role"] = res["role_b"]

                    yield (_id, _src_id, _tar_id, _type, _props)

        self.bcy.write_edges(
            edges=edge_gen(),
            db_name=self.db_name,
        )