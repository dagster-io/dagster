from collections import OrderedDict

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.snap import PipelineIndex

from .external_data import (
    ActivePipelineData,
    ActiveRepositoryData,
    active_pipeline_data_from_def,
    active_repository_data_from_def,
)


class ExternalRepository:
    def __init__(self, active_repository_data):
        self.active_repository_data = check.inst_param(
            active_repository_data, 'active_repository_data', ActiveRepositoryData
        )
        self._pipeline_index_map = OrderedDict(
            (
                active_pipeline_data.pipeline_snapshot.name,
                PipelineIndex(active_pipeline_data.pipeline_snapshot),
            )
            for active_pipeline_data in active_repository_data.active_pipeline_datas
        )

    def get_pipeline_index(self, pipeline_name):
        return self._pipeline_index_map[pipeline_name]

    def has_pipeline(self, pipeline_name):
        return pipeline_name in self._pipeline_index_map

    def get_pipeline_indices(self):
        return self._pipeline_index_map.values()

    @staticmethod
    def from_repository_def(repository_definition):
        return ExternalRepository(active_repository_data_from_def(repository_definition))


class __SolidSubsetNotProvidedSentinel(object):
    pass


SOLID_SUBSET_NOT_PROVIDED = __SolidSubsetNotProvidedSentinel


# Represents a pipeline definition that is resident in an external process.
#
# Object composes a pipeline index (which is an index over snapshot data)
# and the serialized ActivePipelineData
class ExternalPipeline:
    def __init__(
        self, pipeline_index, active_pipeline_data, solid_subset=SOLID_SUBSET_NOT_PROVIDED,
    ):
        self.pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._active_pipeline_data = check.inst_param(
            active_pipeline_data, 'active_pipeline_data', ActivePipelineData
        )
        self._active_preset_dict = {ap.name: ap for ap in active_pipeline_data.active_presets}

        if solid_subset != SOLID_SUBSET_NOT_PROVIDED:
            check.opt_list_param(solid_subset, 'solid_subset', str)

        self._solid_subset = solid_subset

    @property
    def name(self):
        return self.pipeline_index.name

    @property
    def solid_subset(self):
        if self._solid_subset == SOLID_SUBSET_NOT_PROVIDED:
            raise DagsterInvariantViolationError(
                "Cannot access property solid_subset on external pipeline constructed without a "
                "solid subset"
            )

        return self._solid_subset

    @property
    def active_presets(self):
        return self._active_pipeline_data.active_presets

    @property
    def solid_names(self):
        return self.pipeline_index.pipeline_snapshot.solid_names

    @property
    def pipeline_snapshot(self):
        return self.pipeline_index.pipeline_snapshot

    def has_solid_invocation(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        return self.pipeline_index.has_solid_invocation(solid_name)

    def has_preset(self, preset_name):
        check.str_param(preset_name, 'preset_name')
        return preset_name in self._active_preset_dict

    def get_preset(self, preset_name):
        check.str_param(preset_name, 'preset_name')
        return self._active_preset_dict[preset_name]

    def get_mode(self, mode_name):
        check.str_param(mode_name, 'mode_name')
        return self.pipeline_index.get_mode_def_snap(mode_name)

    def root_config_key_for_mode(self, mode_name):
        check.opt_str_param(mode_name, 'mode_name')
        return self.get_mode(
            mode_name if mode_name else self.get_default_mode_name()
        ).root_config_key

    @staticmethod
    def from_pipeline_def(pipeline_def, solid_subset=None):
        if solid_subset:
            pipeline_def = pipeline_def.subset_for_execution(solid_subset)

        return ExternalPipeline(
            pipeline_def.get_pipeline_index(),
            active_pipeline_data_from_def(pipeline_def),
            solid_subset=solid_subset,
        )

    @property
    def config_schema_snapshot(self):
        return self.pipeline_index.pipeline_snapshot.config_schema_snapshot

    @property
    def pipeline_snapshot_id(self):
        return self.pipeline_index.pipeline_snapshot_id

    def get_default_mode_name(self):
        return self.pipeline_index.get_default_mode_name()

    @property
    def tags(self):
        return self.pipeline_index.pipeline_snapshot.tags
