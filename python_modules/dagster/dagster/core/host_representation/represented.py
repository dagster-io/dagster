from abc import ABC, abstractmethod

import dagster._check as check

from .pipeline_index import PipelineIndex


class RepresentedPipeline(ABC):
    """
    RepresentedPipeline is a base class for ExternalPipeline or HistoricalPipeline.

    The name is "represented" because this is an in-memory representation of a pipeline.
    The representation of a pipeline could be referring to a pipeline resident in
    another process *or* could be referring to a historical view of the pipeline.
    """

    def __init__(self, pipeline_index):
        self._pipeline_index = check.inst_param(pipeline_index, "pipeline_index", PipelineIndex)

    # Temporary method to allow for incrementally
    # replacing pipeline index with the representation hierarchy
    # Chosen for grepability
    def get_pipeline_index_for_compat(self):
        return self._pipeline_index

    @property
    def name(self):
        return self._pipeline_index.name

    @property
    def description(self):
        return self._pipeline_index.description

    # Snapshot things

    @property
    @abstractmethod
    def computed_pipeline_snapshot_id(self):
        pass

    @property
    @abstractmethod
    def identifying_pipeline_snapshot_id(self):
        pass

    @property
    def pipeline_snapshot(self):
        return self._pipeline_index.pipeline_snapshot

    @property
    def parent_pipeline_snapshot(self):
        return self._pipeline_index.parent_pipeline_snapshot

    @property
    def solid_selection(self):
        return (
            self._pipeline_index.pipeline_snapshot.lineage_snapshot.solid_selection
            if self._pipeline_index.pipeline_snapshot.lineage_snapshot
            else None
        )

    @property
    def solids_to_execute(self):
        return (
            self._pipeline_index.pipeline_snapshot.lineage_snapshot.solids_to_execute
            if self._pipeline_index.pipeline_snapshot.lineage_snapshot
            else None
        )

    # Config

    @property
    def config_schema_snapshot(self):
        return self._pipeline_index.config_schema_snapshot

    # DagsterTypes

    @property
    def dagster_type_snaps(self):
        return self._pipeline_index.get_dagster_type_snaps()

    def has_dagster_type_named(self, type_name):
        return self._pipeline_index.has_dagster_type_name(type_name)

    def get_dagster_type_by_name(self, type_name):
        return self._pipeline_index.get_dagster_type_from_name(type_name)

    # Modes

    @property
    def mode_def_snaps(self):
        return self._pipeline_index.pipeline_snapshot.mode_def_snaps

    def get_mode_def_snap(self, mode_name):
        return self._pipeline_index.get_mode_def_snap(mode_name)

    # Deps

    @property
    def dep_structure_index(self):
        return self._pipeline_index.dep_structure_index

    # Solids
    def get_node_def_snap(self, solid_def_name):
        check.str_param(solid_def_name, "solid_def_name")
        return self._pipeline_index.get_node_def_snap(solid_def_name)

    def get_dep_structure_index(self, solid_def_name):
        check.str_param(solid_def_name, "solid_def_name")
        return self._pipeline_index.get_dep_structure_index(solid_def_name)

    # Graph

    def get_graph_name(self):
        return self._pipeline_index.pipeline_snapshot.graph_def_name
