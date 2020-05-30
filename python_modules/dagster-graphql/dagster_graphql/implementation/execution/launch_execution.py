from __future__ import absolute_import

import sys

from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.config.validate import validate_config_from_snap
from dagster.core.errors import DagsterInvalidConfigError, DagsterLaunchFailedError
from dagster.core.events import EngineEventData
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

from ..external import (
    ensure_valid_config,
    get_external_execution_plan_or_raise,
    get_external_pipeline_or_raise,
    legacy_get_external_pipeline_or_raise,
)
from ..resume_retry import compute_step_keys_to_execute
from ..utils import (
    ExecutionMetadata,
    ExecutionParams,
    UserFacingGraphQLError,
    capture_dauphin_error,
)


@capture_dauphin_error
def launch_pipeline_reexecution(graphene_info, execution_params):
    return _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=True)


@capture_dauphin_error
def launch_pipeline_execution(graphene_info, execution_params):
    return _launch_pipeline_execution(graphene_info, execution_params)


def do_launch(graphene_info, execution_params, is_reexecuted=False):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    check.bool_param(is_reexecuted, 'is_reexecuted')

    if is_reexecuted:
        # required fields for re-execution
        execution_metadata = check.inst_param(
            execution_params.execution_metadata, 'execution_metadata', ExecutionMetadata
        )
        check.str_param(execution_metadata.root_run_id, 'root_run_id')
        check.str_param(execution_metadata.parent_run_id, 'parent_run_id')

    instance = graphene_info.context.instance

    external_pipeline = get_external_pipeline_or_raise(graphene_info, execution_params.selector)

    ensure_valid_config(external_pipeline, execution_params.mode, execution_params.environment_dict)

    step_keys_to_execute = compute_step_keys_to_execute(
        graphene_info, external_pipeline, execution_params
    )

    external_execution_plan = get_external_execution_plan_or_raise(
        graphene_info=graphene_info,
        external_pipeline=external_pipeline,
        mode=execution_params.mode,
        environment_dict=execution_params.environment_dict,
        step_keys_to_execute=step_keys_to_execute,
    )

    pipeline_run = instance.create_run(
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        pipeline_name=execution_params.selector.pipeline_name,
        run_id=execution_params.execution_metadata.run_id
        if execution_params.execution_metadata.run_id
        else make_new_run_id(),
        solid_subset=execution_params.selector.solid_subset,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
        step_keys_to_execute=step_keys_to_execute,
        tags=merge_dicts(external_pipeline.tags, execution_params.execution_metadata.tags),
        root_run_id=execution_params.execution_metadata.root_run_id,
        parent_run_id=execution_params.execution_metadata.parent_run_id,
        status=PipelineRunStatus.NOT_STARTED,
    )

    return instance.launch_run(pipeline_run.run_id, external_pipeline=external_pipeline)


def _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=False):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    check.bool_param(is_reexecuted, 'is_reexecuted')

    run = do_launch(graphene_info, execution_params, is_reexecuted)

    return graphene_info.schema.type_named('LaunchPipelineRunSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )


# TODO this and _synchronously_execute_run_within_hosted_user_process should share implementation
def do_launch_for_created_run(graphene_info, run_id):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(run_id, 'run_id')

    # First retrieve the pipeline run
    instance = graphene_info.context.instance
    pipeline_run = instance.get_run_by_id(run_id)
    if not pipeline_run:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)
        )

    external_pipeline = legacy_get_external_pipeline_or_raise(
        graphene_info, pipeline_run.pipeline_name, pipeline_run.solid_subset
    )

    # Run config validation
    # If there are any config errors, then inject them into the event log
    validated_config = validate_config_from_snap(
        external_pipeline.config_schema_snapshot,
        external_pipeline.root_config_key_for_mode(pipeline_run.mode),
        pipeline_run.environment_dict,
    )

    if not validated_config.success:
        # If the config is invalid, we construct a DagsterInvalidConfigError exception and
        # insert it into the event log. We also return a PipelineConfigValidationInvalid user facing
        # graphql error.

        # We currently re-use the engine events machinery to add the error to the event log, but
        # may need to create a new event type and instance method to handle these errors.
        invalid_config_exception = DagsterInvalidConfigError(
            'Error in config for pipeline {}'.format(external_pipeline.name),
            validated_config.errors,
            pipeline_run.environment_dict,
        )

        instance.report_engine_event(
            str(invalid_config_exception.message),
            pipeline_run,
            EngineEventData.engine_error(
                SerializableErrorInfo(
                    invalid_config_exception.message,
                    [],
                    DagsterInvalidConfigError.__class__.__name__,
                    None,
                )
            ),
        )

        instance.report_run_failed(pipeline_run)

        return DauphinPipelineConfigValidationInvalid.for_validation_errors(
            external_pipeline, validated_config.errors
        )

    try:
        launched_run = instance.launch_run(pipeline_run.run_id, external_pipeline)
        return graphene_info.schema.type_named('LaunchPipelineRunSuccess')(
            run=graphene_info.schema.type_named('PipelineRun')(launched_run)
        )
    except DagsterLaunchFailedError:
        error = serializable_error_info_from_exc_info(sys.exc_info())
        instance.report_engine_event(
            error.message, pipeline_run, EngineEventData.engine_error(error),
        )
        instance.report_run_failed(pipeline_run)
        # https://github.com/dagster-io/dagster/issues/2508
        # We should return a proper GraphQL error here
        raise
