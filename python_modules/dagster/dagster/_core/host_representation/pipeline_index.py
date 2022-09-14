from threading import Lock
from typing import Any, Mapping, Optional, Sequence, Union

import dagster._check as check
from dagster._config import ConfigSchemaSnapshot
from dagster._core.snap import (
    DependencyStructureIndex,
    PipelineSnapshot,
    create_pipeline_snapshot_id,
)
from dagster._core.snap.dagster_types import DagsterTypeSnap
from dagster._core.snap.mode import ModeDefSnap
from dagster._core.snap.solid import CompositeSolidDefSnap, SolidDefSnap


class PipelineIndex:

    pipeline_snapshot: PipelineSnapshot
    parent_pipeline_snapshot: Optional[PipelineSnapshot]
    _node_defs_snaps_index: Mapping[str, Union[SolidDefSnap, CompositeSolidDefSnap]]
    _dagster_type_snaps_by_name_index: Mapping[str, DagsterTypeSnap]
    dep_structure_index: DependencyStructureIndex
    _comp_dep_structures: Mapping[str, DependencyStructureIndex]
    _pipeline_snapshot_id: Optional[str]

    def __init__(
        self,
        pipeline_snapshot: PipelineSnapshot,
        parent_pipeline_snapshot: Optional[PipelineSnapshot],
    ):
        self.pipeline_snapshot = check.inst_param(
            pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot
        )
        self.parent_pipeline_snapshot = check.opt_inst_param(
            parent_pipeline_snapshot, "parent_pipeline_snapshot", PipelineSnapshot
        )

        if self.pipeline_snapshot.lineage_snapshot:
            check.invariant(
                self.parent_pipeline_snapshot is not None,
                "Can not create PipelineIndex for pipeline_snapshot with lineage without parent_pipeline_snapshot",
            )

        node_def_snaps: Sequence[Union[SolidDefSnap, CompositeSolidDefSnap]] = [
            *pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps,
            *pipeline_snapshot.solid_definitions_snapshot.composite_solid_def_snaps,
        ]
        self._node_defs_snaps_index = {sd.name: sd for sd in node_def_snaps}

        self._dagster_type_snaps_by_name_index = {
            dagster_type_snap.name: dagster_type_snap
            for dagster_type_snap in pipeline_snapshot.dagster_type_namespace_snapshot.all_dagster_type_snaps_by_key.values()
            if dagster_type_snap.name
        }

        self.dep_structure_index = DependencyStructureIndex(
            pipeline_snapshot.dep_structure_snapshot
        )

        self._comp_dep_structures = {
            comp_snap.name: DependencyStructureIndex(comp_snap.dep_structure_snapshot)
            for comp_snap in pipeline_snapshot.solid_definitions_snapshot.composite_solid_def_snaps
        }

        self._memo_lock = Lock()
        self._pipeline_snapshot_id = None

    @property
    def name(self) -> str:
        return self.pipeline_snapshot.name

    @property
    def description(self) -> Optional[str]:
        return self.pipeline_snapshot.description

    @property
    def tags(self) -> Mapping[str, Any]:
        return self.pipeline_snapshot.tags

    @property
    def metadata(self):
        return self.pipeline_snapshot.metadata

    @property
    def pipeline_snapshot_id(self) -> str:
        with self._memo_lock:
            if not self._pipeline_snapshot_id:
                self._pipeline_snapshot_id = create_pipeline_snapshot_id(self.pipeline_snapshot)
            return self._pipeline_snapshot_id

    def has_dagster_type_name(self, type_name: str) -> bool:
        return type_name in self._dagster_type_snaps_by_name_index

    def get_dagster_type_from_name(self, type_name: str) -> DagsterTypeSnap:
        return self._dagster_type_snaps_by_name_index[type_name]

    def get_node_def_snap(self, node_def_name: str) -> Union[SolidDefSnap, CompositeSolidDefSnap]:
        check.str_param(node_def_name, "node_def_name")
        return self._node_defs_snaps_index[node_def_name]

    def get_dep_structure_index(self, comp_solid_def_name: str) -> DependencyStructureIndex:
        return self._comp_dep_structures[comp_solid_def_name]

    def get_dagster_type_snaps(self) -> Sequence[DagsterTypeSnap]:
        dt_namespace = self.pipeline_snapshot.dagster_type_namespace_snapshot
        return list(dt_namespace.all_dagster_type_snaps_by_key.values())

    def has_solid_invocation(self, solid_name: str) -> bool:
        return self.dep_structure_index.has_invocation(solid_name)

    def get_default_mode_name(self) -> str:
        return self.pipeline_snapshot.mode_def_snaps[0].name

    def has_mode_def(self, name: str) -> bool:
        check.str_param(name, "name")
        for mode_def_snap in self.pipeline_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return True

        return False

    @property
    def available_modes(self) -> Sequence[str]:
        return [mode_def_snap.name for mode_def_snap in self.pipeline_snapshot.mode_def_snaps]

    def get_mode_def_snap(self, name: str) -> ModeDefSnap:
        check.str_param(name, "name")
        for mode_def_snap in self.pipeline_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return mode_def_snap

        check.failed("Mode {mode} not found".format(mode=name))

    @property
    def config_schema_snapshot(self) -> ConfigSchemaSnapshot:
        return self.pipeline_snapshot.config_schema_snapshot
