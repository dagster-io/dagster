from abc import ABC, abstractmethod
from typing import AbstractSet, Optional, Sequence, Union

import dagster._check as check
from dagster._config import ConfigSchemaSnapshot
from dagster._core.snap.dagster_types import DagsterTypeSnap
from dagster._core.snap.dep_snapshot import DependencyStructureIndex
from dagster._core.snap.mode import ModeDefSnap
from dagster._core.snap.pipeline_snapshot import PipelineSnapshot
from dagster._core.snap.solid import CompositeSolidDefSnap, SolidDefSnap

from .pipeline_index import PipelineIndex


class RepresentedPipeline(ABC):
    """
    RepresentedPipeline is a base class for ExternalPipeline or HistoricalPipeline.

    The name is "represented" because this is an in-memory representation of a pipeline.
    The representation of a pipeline could be referring to a pipeline resident in
    another process *or* could be referring to a historical view of the pipeline.
    """

    @property
    @abstractmethod
    def _pipeline_index(self) -> PipelineIndex:
        ...

    @property
    def name(self) -> str:
        return self._pipeline_index.name

    @property
    def description(self) -> Optional[str]:
        return self._pipeline_index.description

    # Snapshot things

    @property
    @abstractmethod
    def computed_pipeline_snapshot_id(self) -> str:
        pass

    @property
    @abstractmethod
    def identifying_pipeline_snapshot_id(self) -> str:
        pass

    @property
    def pipeline_snapshot(self) -> PipelineSnapshot:
        return self._pipeline_index.pipeline_snapshot

    @property
    def parent_pipeline_snapshot(self) -> Optional[PipelineSnapshot]:
        return self._pipeline_index.parent_pipeline_snapshot

    @property
    def solid_selection(self) -> Optional[Sequence[str]]:
        return (
            self._pipeline_index.pipeline_snapshot.lineage_snapshot.solid_selection
            if self._pipeline_index.pipeline_snapshot.lineage_snapshot
            else None
        )

    @property
    def solids_to_execute(self) -> Optional[AbstractSet[str]]:
        return (
            self._pipeline_index.pipeline_snapshot.lineage_snapshot.solids_to_execute
            if self._pipeline_index.pipeline_snapshot.lineage_snapshot
            else None
        )

    # Config

    @property
    def config_schema_snapshot(self) -> ConfigSchemaSnapshot:
        return self._pipeline_index.config_schema_snapshot

    # DagsterTypes

    @property
    def dagster_type_snaps(self) -> Sequence[DagsterTypeSnap]:
        return self._pipeline_index.get_dagster_type_snaps()

    def has_dagster_type_named(self, type_name: str) -> bool:
        return self._pipeline_index.has_dagster_type_name(type_name)

    def get_dagster_type_by_name(self, type_name: str) -> DagsterTypeSnap:
        return self._pipeline_index.get_dagster_type_from_name(type_name)

    # Modes

    @property
    def mode_def_snaps(self) -> Sequence[ModeDefSnap]:
        return self._pipeline_index.pipeline_snapshot.mode_def_snaps

    def get_mode_def_snap(self, mode_name: str) -> ModeDefSnap:
        return self._pipeline_index.get_mode_def_snap(mode_name)

    # Deps

    @property
    def dep_structure_index(self) -> DependencyStructureIndex:
        return self._pipeline_index.dep_structure_index

    # Solids
    def get_node_def_snap(self, solid_def_name: str) -> Union[SolidDefSnap, CompositeSolidDefSnap]:
        check.str_param(solid_def_name, "solid_def_name")
        return self._pipeline_index.get_node_def_snap(solid_def_name)

    def get_dep_structure_index(self, solid_def_name: str) -> DependencyStructureIndex:
        check.str_param(solid_def_name, "solid_def_name")
        return self._pipeline_index.get_dep_structure_index(solid_def_name)

    # Graph

    def get_graph_name(self) -> str:
        return self._pipeline_index.pipeline_snapshot.graph_def_name
