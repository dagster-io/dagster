import sys

from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.config.validate import validate_config_from_snap
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.core.snap import (
    ActivePipelineData,
    ExecutionPlanIndex,
    PipelineIndex,
    active_pipeline_data_from_def,
)
from dagster.utils.error import serializable_error_info_from_exc_info

from .utils import UserFacingGraphQLError


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

    @staticmethod
    def from_pipeline_def(pipeline_def, solid_subset=None):
        if solid_subset:
            pipeline_def = pipeline_def.build_sub_pipeline(solid_subset)

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


def get_external_pipeline_or_raise(graphene_info, pipeline_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)

    if not graphene_info.context.has_external_pipeline(pipeline_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=pipeline_name)
        )

    return graphene_info.context.get_external_pipeline(pipeline_name)


def get_external_pipeline_subset_or_raise(graphene_info, pipeline_name, solid_subset):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(pipeline_name, 'pipeline_name')
    check.opt_list_param(solid_subset, 'solid_subset', of_type=str)

    from dagster_graphql.schema.errors import DauphinInvalidSubsetError

    full_pipeline = get_external_pipeline_or_raise(graphene_info, pipeline_name)

    if solid_subset is None:
        return full_pipeline

    for solid_name in solid_subset:
        if not full_pipeline.has_solid_invocation(solid_name):
            raise UserFacingGraphQLError(
                DauphinInvalidSubsetError(
                    message='Solid "{solid_name}" does not exist in "{pipeline_name}"'.format(
                        solid_name=solid_name, pipeline_name=pipeline_name
                    ),
                    pipeline=graphene_info.schema.type_named('Pipeline')(full_pipeline),
                )
            )
    try:
        return graphene_info.context.get_external_pipeline_subset(pipeline_name, solid_subset)
    except DagsterInvalidDefinitionError:
        # this handles the case when you construct a subset such that an unsatisfied
        # input cannot be hydrate from config. Current this is only relevant for
        # the in-process case. Once we add the out-of-process we will communicate
        # this error through the communication channel and change what exception
        # is thrown
        raise UserFacingGraphQLError(
            DauphinInvalidSubsetError(
                message=serializable_error_info_from_exc_info(sys.exc_info()).message,
                pipeline=graphene_info.schema.type_named('Pipeline')(full_pipeline),
            )
        )


def ensure_valid_config(external_pipeline, mode, environment_dict):
    check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
    check.str_param(mode, 'mode')
    # do not type check environment_dict so that validate_config_from_snap throws

    validated_config = validate_config_from_snap(
        config_schema_snapshot=external_pipeline.config_schema_snapshot,
        config_type_key=external_pipeline.pipeline_index.get_mode_def_snap(mode).root_config_key,
        config_value=environment_dict,
    )

    if not validated_config.success:
        from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid

        raise UserFacingGraphQLError(
            DauphinPipelineConfigValidationInvalid.for_validation_errors(
                external_pipeline.pipeline_index, validated_config.errors
            )
        )

    return validated_config


def ensure_valid_step_keys(full_execution_plan_index, step_keys):
    check.inst_param(full_execution_plan_index, 'full_execution_plan_index', ExecutionPlanIndex)
    check.opt_list_param(step_keys, 'step_keys', of_type=str)

    if not step_keys:
        return

    for step_key in step_keys:
        if not full_execution_plan_index.has_step(step_key):
            from dagster_graphql.schema.errors import DauphinInvalidStepError

            raise UserFacingGraphQLError(DauphinInvalidStepError(invalid_step_key=step_key))


def get_execution_plan_index_or_raise(
    graphene_info, external_pipeline, mode, environment_dict, step_keys_to_execute
):
    full_execution_plan_index = graphene_info.context.create_execution_plan_index(
        external_pipeline=external_pipeline, environment_dict=environment_dict, mode=mode,
    )

    if not step_keys_to_execute:
        return full_execution_plan_index

    ensure_valid_step_keys(full_execution_plan_index, step_keys_to_execute)

    return graphene_info.context.create_execution_plan_index(
        external_pipeline=external_pipeline,
        environment_dict=environment_dict,
        mode=mode,
        step_keys_to_execute=step_keys_to_execute,
    )
