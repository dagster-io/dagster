from abc import ABC, abstractmethod
from typing import AbstractSet, Optional, Sequence, Union

import dagster._check as check
from dagster._config import ConfigSchemaSnapshot
from dagster._core.snap.dagster_types import DagsterTypeSnap
from dagster._core.snap.dep_snapshot import DependencyStructureIndex
from dagster._core.snap.job_snapshot import JobSnapshot
from dagster._core.snap.mode import ModeDefSnap
from dagster._core.snap.node import GraphDefSnap, OpDefSnap

from .job_index import JobIndex


class RepresentedJob(ABC):
    """RepresentedJob is a base class for ExternalPipeline or HistoricalPipeline.

    The name is "represented" because this is an in-memory representation of a job.
    The representation of a job could be referring to a job resident in
    another process *or* could be referring to a historical view of the job.
    """

    @property
    @abstractmethod
    def _job_index(self) -> JobIndex:
        ...

    @property
    def name(self) -> str:
        return self._job_index.name

    @property
    def description(self) -> Optional[str]:
        return self._job_index.description

    # Snapshot things

    @property
    @abstractmethod
    def computed_job_snapshot_id(self) -> str:
        pass

    @property
    @abstractmethod
    def identifying_job_snapshot_id(self) -> str:
        pass

    @property
    def job_snapshot(self) -> JobSnapshot:
        return self._job_index.job_snapshot

    @property
    def parent_job_snapshot(self) -> Optional[JobSnapshot]:
        return self._job_index.parent_job_snapshot

    @property
    def solid_selection(self) -> Optional[Sequence[str]]:
        return (
            self._job_index.job_snapshot.lineage_snapshot.node_selection
            if self._job_index.job_snapshot.lineage_snapshot
            else None
        )

    @property
    def solids_to_execute(self) -> Optional[AbstractSet[str]]:
        return (
            self._job_index.job_snapshot.lineage_snapshot.nodes_to_execute
            if self._job_index.job_snapshot.lineage_snapshot
            else None
        )

    # Config

    @property
    def config_schema_snapshot(self) -> ConfigSchemaSnapshot:
        return self._job_index.config_schema_snapshot

    # DagsterTypes

    @property
    def dagster_type_snaps(self) -> Sequence[DagsterTypeSnap]:
        return self._job_index.get_dagster_type_snaps()

    def has_dagster_type_named(self, type_name: str) -> bool:
        return self._job_index.has_dagster_type_name(type_name)

    def get_dagster_type_by_name(self, type_name: str) -> DagsterTypeSnap:
        return self._job_index.get_dagster_type_from_name(type_name)

    # Modes

    @property
    def mode_def_snaps(self) -> Sequence[ModeDefSnap]:
        return self._job_index.job_snapshot.mode_def_snaps

    def get_mode_def_snap(self, mode_name: str) -> ModeDefSnap:
        return self._job_index.get_mode_def_snap(mode_name)

    # Deps

    @property
    def dep_structure_index(self) -> DependencyStructureIndex:
        return self._job_index.dep_structure_index

    # Nodes
    def get_node_def_snap(self, node_def_name: str) -> Union[OpDefSnap, GraphDefSnap]:
        check.str_param(node_def_name, "node_def_name")
        return self._job_index.get_node_def_snap(node_def_name)

    def get_dep_structure_index(self, node_def_name: str) -> DependencyStructureIndex:
        check.str_param(node_def_name, "node_def_name")
        return self._job_index.get_dep_structure_index(node_def_name)

    # Graph

    def get_graph_name(self) -> str:
        return self._job_index.job_snapshot.graph_def_name
