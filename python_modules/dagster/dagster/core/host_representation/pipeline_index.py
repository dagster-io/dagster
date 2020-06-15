from dagster import check
from dagster.core.snap import DependencyStructureIndex, PipelineSnapshotWithID


class PipelineIndex:
    def __init__(self, pipeline_snapshot_with_id, parent_pipeline_snapshot_with_id):
        self.pipeline_snapshot_with_id = check.inst_param(
            pipeline_snapshot_with_id, 'pipeline_snapshot_with_id', PipelineSnapshotWithID
        )
        self.parent_pipeline_snapshot_with_id = check.opt_inst_param(
            parent_pipeline_snapshot_with_id,
            'parent_pipeline_snapshot_with_id',
            PipelineSnapshotWithID,
        )

        pipeline_snapshot = pipeline_snapshot_with_id.pipeline_snapshot
        parent_pipeline_snapshot = (
            parent_pipeline_snapshot_with_id.pipeline_snapshot
            if parent_pipeline_snapshot_with_id
            else None
        )

        if pipeline_snapshot.lineage_snapshot:
            check.invariant(
                parent_pipeline_snapshot is not None,
                'Can not create PipelineIndex for pipeline_snapshot with '
                'lineage without parent_pipeline_snapshot',
            )
            check.invariant(
                pipeline_snapshot.lineage_snapshot.parent_snapshot_id
                == parent_pipeline_snapshot_with_id.pipeline_snapshot_id,
                'Mismatch in IDs between pipeline_snapshot lineage and parent_pipeline_snapshot',
            )

        self._solid_defs_snaps_index = {
            sd.name: sd
            for sd in pipeline_snapshot.solid_definitions_snapshot.solid_def_snaps
            + pipeline_snapshot.solid_definitions_snapshot.composite_solid_def_snaps
        }

        all_dagster_type_snaps = (
            pipeline_snapshot.dagster_type_namespace_snapshot.all_dagster_type_snaps_by_key
        ).values()

        self._dagster_type_snaps_by_name_index = {
            dagster_type_snap.name: dagster_type_snap
            for dagster_type_snap in all_dagster_type_snaps
            if dagster_type_snap.name
        }

        self.dep_structure_index = DependencyStructureIndex(
            pipeline_snapshot.dep_structure_snapshot
        )

        self._comp_dep_structures = {
            comp_snap.name: DependencyStructureIndex(comp_snap.dep_structure_snapshot)
            for comp_snap in pipeline_snapshot.solid_definitions_snapshot.composite_solid_def_snaps
        }

    @property
    def pipeline_snapshot(self):
        return self.pipeline_snapshot_with_id.pipeline_snapshot

    @property
    def parent_pipeline_snapshot(self):
        return (
            self.parent_pipeline_snapshot_with_id.pipeline_snapshot
            if self.parent_pipeline_snapshot_with_id
            else None
        )

    @property
    def pipeline_snapshot_id(self):
        return self.pipeline_snapshot_with_id.pipeline_snapshot_id

    @property
    def name(self):
        return self.pipeline_snapshot.name

    @property
    def description(self):
        return self.pipeline_snapshot.description

    @property
    def tags(self):
        return self.pipeline_snapshot.tags

    def has_dagster_type_name(self, type_name):
        return type_name in self._dagster_type_snaps_by_name_index

    def get_dagster_type_from_name(self, type_name):
        return self._dagster_type_snaps_by_name_index[type_name]

    def get_solid_def_snap(self, solid_def_name):
        check.str_param(solid_def_name, 'solid_def_name')
        return self._solid_defs_snaps_index[solid_def_name]

    def get_dep_structure_index(self, comp_solid_def_name):
        return self._comp_dep_structures[comp_solid_def_name]

    def get_dagster_type_snaps(self):
        dt_namespace = self.pipeline_snapshot.dagster_type_namespace_snapshot
        return list(dt_namespace.all_dagster_type_snaps_by_key.values())

    def has_solid_invocation(self, solid_name):
        return self.dep_structure_index.has_invocation(solid_name)

    def get_default_mode_name(self):
        return self.pipeline_snapshot.mode_def_snaps[0].name

    def has_mode_def(self, name):
        check.str_param(name, 'name')
        for mode_def_snap in self.pipeline_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return True

        return False

    def get_mode_def_snap(self, name):
        check.str_param(name, 'name')
        for mode_def_snap in self.pipeline_snapshot.mode_def_snaps:
            if mode_def_snap.name == name:
                return mode_def_snap

        check.failed('Mode {mode} not found'.format(mode=name))

    @property
    def config_schema_snapshot(self):
        return self.pipeline_snapshot.config_schema_snapshot
