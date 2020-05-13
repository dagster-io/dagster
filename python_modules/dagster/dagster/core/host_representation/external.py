from collections import OrderedDict

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.snap import ExecutionPlanSnapshot, snapshot_from_execution_plan

from .external_data import (
    ExternalPipelineData,
    ExternalRepositoryData,
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from .historical import RepresentedPipeline
from .pipeline_index import PipelineIndex


class ExternalRepository:
    def __init__(self, external_repository_data):
        self.external_repository_data = check.inst_param(
            external_repository_data, 'external_repository_data', ExternalRepositoryData
        )
        self._pipeline_index_map = OrderedDict(
            (
                external_pipeline_data.pipeline_snapshot.name,
                PipelineIndex(external_pipeline_data.pipeline_snapshot),
            )
            for external_pipeline_data in external_repository_data.external_pipeline_datas
        )

    def get_pipeline_index(self, pipeline_name):
        return self._pipeline_index_map[pipeline_name]

    def has_pipeline(self, pipeline_name):
        return pipeline_name in self._pipeline_index_map

    def get_pipeline_indices(self):
        return self._pipeline_index_map.values()

    @staticmethod
    def from_repository_def(repository_definition):
        return ExternalRepository(external_repository_data_from_def(repository_definition))


class __SolidSubsetNotProvidedSentinel(object):
    pass


SOLID_SUBSET_NOT_PROVIDED = __SolidSubsetNotProvidedSentinel


# Represents a pipeline definition that is resident in an external process.
#
# Object composes a pipeline index (which is an index over snapshot data)
# and the serialized ExternalPipelineData
class ExternalPipeline(RepresentedPipeline):
    def __init__(
        self, pipeline_index, external_pipeline_data, solid_subset=SOLID_SUBSET_NOT_PROVIDED,
    ):
        self.pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._external_pipeline_data = check.inst_param(
            external_pipeline_data, 'external_pipeline_data', ExternalPipelineData
        )
        self._active_preset_dict = {ap.name: ap for ap in external_pipeline_data.active_presets}

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
        return self._external_pipeline_data.active_presets

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

    def get_mode_def_snap(self, mode_name):
        check.str_param(mode_name, 'mode_name')
        return self.pipeline_index.get_mode_def_snap(mode_name)

    def has_mode(self, mode_name):
        check.str_param(mode_name, 'mode_name')
        return self.pipeline_index.has_mode_def(mode_name)

    def root_config_key_for_mode(self, mode_name):
        check.opt_str_param(mode_name, 'mode_name')
        return self.get_mode_def_snap(
            mode_name if mode_name else self.get_default_mode_name()
        ).root_config_key

    @staticmethod
    def from_pipeline_def(pipeline_def, solid_subset=None):
        if solid_subset:
            pipeline_def = pipeline_def.subset_for_execution(solid_subset)

        return ExternalPipeline(
            pipeline_def.get_pipeline_index(),
            external_pipeline_data_from_def(pipeline_def),
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


class ExternalExecutionPlan:
    def __init__(self, execution_plan_snapshot, pipeline_index):

        self.execution_plan_snapshot = check.inst_param(
            execution_plan_snapshot, 'execution_plan_snapshot', ExecutionPlanSnapshot
        )
        self.pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)

        self._step_index = {step.key: step for step in self.execution_plan_snapshot.steps}

        # https://github.com/dagster-io/dagster/issues/2442
        # check.invariant(
        #     execution_plan_snapshot.pipeline_snapshot_id == pipeline_index.pipeline_snapshot_id
        # )

        self._step_keys_in_plan = (
            set(execution_plan_snapshot.step_keys_to_execute)
            if execution_plan_snapshot.step_keys_to_execute
            else set(self._step_index.keys())
        )

    def has_step(self, key):
        check.str_param(key, 'key')
        return key in self._step_index

    def get_step_by_key(self, key):
        check.str_param(key, 'key')
        return self._step_index[key]

    @staticmethod
    def from_plan_and_index(execution_plan, pipeline_index):
        from dagster.core.execution.plan.plan import ExecutionPlan

        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        return ExternalExecutionPlan(
            snapshot_from_execution_plan(
                execution_plan=execution_plan,
                pipeline_snapshot_id=pipeline_index.pipeline_snapshot_id,
            ),
            pipeline_index,
        )

    def get_steps_in_plan(self):
        return [self._step_index[sk] for sk in self._step_keys_in_plan]

    def key_in_plan(self, key):
        return key in self._step_keys_in_plan
