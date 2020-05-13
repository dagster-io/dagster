from abc import ABCMeta

import six

from dagster import check

from .pipeline_index import PipelineIndex


class RepresentedPipeline(six.with_metaclass(ABCMeta)):
    def __init__(self, pipeline_index):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)

    # Temporary method to allow for incrementally
    # replacing pipeline index with the representation hierarchy
    # Chosen for greppability
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
    def pipeline_snapshot_id(self):
        return self._pipeline_index.pipeline_snapshot_id

    @property
    def pipeline_snapshot(self):
        return self._pipeline_index.pipeline_snapshot

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
    def get_solid_def_snap(self, solid_def_name):
        check.str_param(solid_def_name, 'solid_def_name')
        return self._pipeline_index.get_solid_def_snap(solid_def_name)

    def get_dep_structure_index(self, solid_def_name):
        check.str_param(solid_def_name, 'solid_def_name')
        return self._pipeline_index.get_dep_structure_index(solid_def_name)
