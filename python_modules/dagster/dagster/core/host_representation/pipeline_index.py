import dagster._check as check
from dagster.core.snap import (
    DependencyStructureIndex,
    PipelineSnapshot,
    create_pipeline_snapshot_id,
)


class PipelineIndex:
    def __init__(self, pipeline_snapshot, parent_pipeline_snapshot):
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

        self._node_defs_snaps_index = {
            sd.name: sd
            for sd in pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps
            + pipeline_snapshot.solid_definitions_snapshot.composite_solid_def_snaps
        }

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

        self._pipeline_snapshot_id = None

    @property
    def name(self):
        return self.pipeline_snapshot.name

    @property
    def description(self):
        return self.pipeline_snapshot.description

    @property
    def tags(self):
        return self.pipeline_snapshot.tags

    @property
    def pipeline_snapshot_id(self):
        if not self._pipeline_snapshot_id:
            self._pipeline_snapshot_id = create_pipeline_snapshot_id(self.pipeline_snapshot)
        return self._pipeline_snapshot_id

    def has_dagster_type_name(self, type_name):
        return type_name in self._dagster_type_snaps_by_name_index

    def get_dagster_type_from_name(self, type_name):
        return self._dagster_type_snaps_by_name_index[type_name]

    def get_node_def_snap(self, node_def_name):
        check.str_param(node_def_name, "node_def_name")
        return self._node_defs_snaps_index[node_def_name]

    def get_dep_structure_index(self, comp_solid_def_name):
        return self._comp_dep_structures[comp_solid_def_name]

    def get_dagster_type_snaps(self):
        dt_namespace = self.pipeline_snapshot.dagster_type_namespace_snapshot
        return list(dt_namespace.all_dagster_type_snaps_by_key.values())

    def has_solid_invocation(self, solid_name):
        return self.dep_structure_index.has_invocation(solid_name)

    def get_default_mode_name(self) -> str:
        return self.pipeline_snapshot.mode_def_snaps[0].name

    def has_mode_def(self, name):
        check.str_param(name, "name")
        for mode_def_snap in self.pipeline_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return True

        return False

    @property
    def available_modes(self):
        return [mode_def_snap.name for mode_def_snap in self.pipeline_snapshot.mode_def_snaps]

    def get_mode_def_snap(self, name):
        check.str_param(name, "name")
        for mode_def_snap in self.pipeline_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return mode_def_snap

        check.failed("Mode {mode} not found".format(mode=name))

    @property
    def config_schema_snapshot(self):
        return self.pipeline_snapshot.config_schema_snapshot
