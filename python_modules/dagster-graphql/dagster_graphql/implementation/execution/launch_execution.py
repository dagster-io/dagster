from __future__ import absolute_import

import sys

from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.config.validate import validate_config
from dagster.core.definitions.environment_schema import create_environment_schema
from dagster.core.errors import DagsterInvalidConfigError, DagsterLaunchFailedError
from dagster.core.events import EngineEventData
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info

from ..external import get_execution_plan_index_or_raise
from ..fetch_pipelines import get_external_pipeline_subset_or_raise, get_pipeline_def_from_selector
from ..fetch_runs import get_validated_config
from ..utils import ExecutionMetadata, ExecutionParams, capture_dauphin_error
from .utils import get_step_keys_to_execute, pipeline_run_args_from_execution_params


@capture_dauphin_error
def launch_pipeline_reexecution(graphene_info, execution_params):
    return _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=True)


@capture_dauphin_error
def launch_pipeline_execution(graphene_info, execution_params):
    return _launch_pipeline_execution(graphene_info, execution_params)


def _launch_pipeline_execution(graphene_info, execution_params, is_reexecuted=False):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    if is_reexecuted:
        # required fields for re-execution
        execution_metadata = check.inst_param(
            execution_params.execution_metadata, 'execution_metadata', ExecutionMetadata
        )
        check.str_param(execution_metadata.root_run_id, 'root_run_id')
        check.str_param(execution_metadata.parent_run_id, 'parent_run_id')

    instance = graphene_info.context.instance
    run_launcher = instance.run_launcher

    if run_launcher is None:
        return graphene_info.schema.type_named('RunLauncherNotDefinedError')()

    external_pipeline = get_external_pipeline_subset_or_raise(
        graphene_info, execution_params.selector.name, execution_params.selector.solid_subset
    )

    pipeline_def = get_pipeline_def_from_selector(graphene_info, execution_params.selector)

    get_validated_config(
        pipeline_def,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
    )

    step_keys_to_execute = get_step_keys_to_execute(instance, pipeline_def, execution_params)

    execution_plan_index = get_execution_plan_index_or_raise(
        graphene_info=graphene_info,
        external_pipeline=external_pipeline,
        mode=execution_params.mode,
        environment_dict=execution_params.environment_dict,
        step_keys_to_execute=step_keys_to_execute,
    )

    pipeline_run = instance.create_run(
        pipeline_snapshot=pipeline_def.get_pipeline_snapshot(),
        execution_plan_snapshot=execution_plan_index.execution_plan_snapshot,
        **pipeline_run_args_from_execution_params(execution_params, step_keys_to_execute)
    )

    run = instance.launch_run(pipeline_run.run_id)

    return graphene_info.schema.type_named('LaunchPipelineRunSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )


def _launch_pipeline_execution_for_created_run(graphene_info, run_id):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(run_id, 'run_id')

    # First retrieve the pipeline run
    instance = graphene_info.context.instance
    pipeline_run = instance.get_run_by_id(run_id)
    if not pipeline_run:
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)

    pipeline_def = get_pipeline_def_from_selector(graphene_info, pipeline_run.selector)

    # Run config valudation
    # If there are any config errors, then inject them into the event log
    environment_schema = create_environment_schema(pipeline_def, pipeline_run.mode)
    validated_config = validate_config(
        environment_schema.environment_type, pipeline_run.environment_dict
    )
    if not validated_config.success:
        # If the config is invalid, we construct a DagsterInvalidConfigError exception and
        # insert it into the event log. We also return a PipelineConfigValidationInvalid user facing
        # graphql error.

        # We currently re-use the engine events machinery to add the error to the event log, but
        # may need to create a new event type and instance method to handle these erros.
        invalid_config_exception = DagsterInvalidConfigError(
            'Error in config for pipeline {}'.format(pipeline_def.name),
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
            pipeline_def.get_pipeline_index(), validated_config.errors
        )

    try:
        pipeline_run = instance.launch_run(pipeline_run.run_id)
    except DagsterLaunchFailedError:
        error = serializable_error_info_from_exc_info(sys.exc_info())
        instance.report_engine_event(
            error.message, pipeline_run, EngineEventData.engine_error(error),
        )
        instance.report_run_failed(pipeline_run)

    return graphene_info.schema.type_named('LaunchPipelineRunSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(pipeline_run)
    )
