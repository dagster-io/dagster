from threading import Lock
from typing import Any, Mapping, Optional, Sequence, Union

import dagster._check as check
from dagster._config import ConfigSchemaSnapshot
from dagster._core.snap import (
    DependencyStructureIndex,
    JobSnapshot,
    create_job_snapshot_id,
)
from dagster._core.snap.dagster_types import DagsterTypeSnap
from dagster._core.snap.mode import ModeDefSnap
from dagster._core.snap.node import GraphDefSnap, OpDefSnap


class JobIndex:
    job_snapshot: JobSnapshot
    parent_job_snapshot: Optional[JobSnapshot]
    _node_defs_snaps_index: Mapping[str, Union[OpDefSnap, GraphDefSnap]]
    _dagster_type_snaps_by_name_index: Mapping[str, DagsterTypeSnap]
    dep_structure_index: DependencyStructureIndex
    _comp_dep_structures: Mapping[str, DependencyStructureIndex]
    _job_snapshot_id: Optional[str]

    def __init__(
        self,
        job_snapshot: JobSnapshot,
        parent_job_snapshot: Optional[JobSnapshot],
    ):
        self.job_snapshot = check.inst_param(job_snapshot, "job_snapshot", JobSnapshot)
        self.parent_job_snapshot = check.opt_inst_param(
            parent_job_snapshot, "parent_job_snapshot", JobSnapshot
        )

        if self.job_snapshot.lineage_snapshot:
            check.invariant(
                self.parent_job_snapshot is not None,
                "Can not create JobIndex for job_snapshot with lineage without parent_job_snapshot",
            )

        node_def_snaps: Sequence[Union[OpDefSnap, GraphDefSnap]] = [
            *job_snapshot.node_defs_snapshot.op_def_snaps,
            *job_snapshot.node_defs_snapshot.graph_def_snaps,
        ]
        self._node_defs_snaps_index = {sd.name: sd for sd in node_def_snaps}

        self._dagster_type_snaps_by_name_index = {
            dagster_type_snap.name: dagster_type_snap
            for dagster_type_snap in job_snapshot.dagster_type_namespace_snapshot.all_dagster_type_snaps_by_key.values()
            if dagster_type_snap.name
        }

        self.dep_structure_index = DependencyStructureIndex(job_snapshot.dep_structure_snapshot)

        self._comp_dep_structures = {
            comp_snap.name: DependencyStructureIndex(comp_snap.dep_structure_snapshot)
            for comp_snap in job_snapshot.node_defs_snapshot.graph_def_snaps
        }

        self._memo_lock = Lock()
        self._job_snapshot_id = None

    @property
    def name(self) -> str:
        return self.job_snapshot.name

    @property
    def description(self) -> Optional[str]:
        return self.job_snapshot.description

    @property
    def tags(self) -> Mapping[str, Any]:
        return self.job_snapshot.tags

    @property
    def metadata(self):
        return self.job_snapshot.metadata

    @property
    def job_snapshot_id(self) -> str:
        with self._memo_lock:
            if not self._job_snapshot_id:
                self._job_snapshot_id = create_job_snapshot_id(self.job_snapshot)
            return self._job_snapshot_id

    def has_dagster_type_name(self, type_name: str) -> bool:
        return type_name in self._dagster_type_snaps_by_name_index

    def get_dagster_type_from_name(self, type_name: str) -> DagsterTypeSnap:
        return self._dagster_type_snaps_by_name_index[type_name]

    def get_node_def_snap(self, node_def_name: str) -> Union[OpDefSnap, GraphDefSnap]:
        check.str_param(node_def_name, "node_def_name")
        return self._node_defs_snaps_index[node_def_name]

    def get_dep_structure_index(self, graph_def_name: str) -> DependencyStructureIndex:
        return self._comp_dep_structures[graph_def_name]

    def get_dagster_type_snaps(self) -> Sequence[DagsterTypeSnap]:
        dt_namespace = self.job_snapshot.dagster_type_namespace_snapshot
        return list(dt_namespace.all_dagster_type_snaps_by_key.values())

    def has_node_invocation(self, node_name: str) -> bool:
        return self.dep_structure_index.has_invocation(node_name)

    def get_default_mode_name(self) -> str:
        return self.job_snapshot.mode_def_snaps[0].name

    def has_mode_def(self, name: str) -> bool:
        check.str_param(name, "name")
        for mode_def_snap in self.job_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return True

        return False

    @property
    def available_modes(self) -> Sequence[str]:
        return [mode_def_snap.name for mode_def_snap in self.job_snapshot.mode_def_snaps]

    def get_mode_def_snap(self, name: str) -> ModeDefSnap:
        check.str_param(name, "name")
        for mode_def_snap in self.job_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return mode_def_snap

        check.failed(f"Mode {name} not found")

    @property
    def config_schema_snapshot(self) -> ConfigSchemaSnapshot:
        return self.job_snapshot.config_schema_snapshot
