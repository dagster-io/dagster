from __future__ import absolute_import

from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid
from graphql.execution.base import ResolveInfo

from dagster import DagsterInvalidConfigError, check
from dagster.config.validate import validate_config
from dagster.core.definitions.environment_schema import create_environment_schema
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import InstanceCreateRunArgs
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.utils import make_new_run_id
from dagster.utils.error import SerializableErrorInfo

from ..fetch_pipelines import get_pipeline_def_from_selector
from ..fetch_runs import get_validated_config
from ..utils import ExecutionMetadata, ExecutionParams, capture_dauphin_error
from .utils import (
    _check_start_pipeline_execution_errors,
    _create_pipeline_run,
    get_step_keys_to_execute,
)


@capture_dauphin_error
def start_pipeline_reexecution(graphene_info, execution_params):
    return _start_pipeline_execution(graphene_info, execution_params, is_reexecuted=True)


@capture_dauphin_error
def start_pipeline_execution(graphene_info, execution_params):
    '''This indirection done on purpose to make the logic in the function
    below re-usable. The parent function is wrapped in @capture_dauphin_error, which makes it
    difficult to do exception handling.
    '''
    return _start_pipeline_execution(graphene_info, execution_params)


def _start_pipeline_execution(graphene_info, execution_params, is_reexecuted=False):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    if is_reexecuted:
        # required fields for re-execution
        execution_metadata = check.inst_param(
            execution_params.execution_metadata, 'execution_metadata', ExecutionMetadata
        )
        check.str_param(execution_metadata.root_run_id, 'root_run_id')
        check.str_param(execution_metadata.parent_run_id, 'parent_run_id')

    error_type = (
        'StartPipelineExecutionDisabledError'
        if not is_reexecuted
        else 'DauphinStartPipelineReexecutionDisabledError'
    )
    success_type = (
        'StartPipelineExecutionSuccess' if not is_reexecuted else 'StartPipelineReexecutionSuccess'
    )

    instance = graphene_info.context.instance

    execution_manager_settings = instance.dagit_settings.get('execution_manager')
    if execution_manager_settings and execution_manager_settings.get('disabled'):
        return graphene_info.schema.type_named(error_type)()

    pipeline_def = get_pipeline_def_from_selector(graphene_info, execution_params.selector)

    get_validated_config(
        pipeline_def,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
    )

    execution_plan = create_execution_plan(
        pipeline_def,
        execution_params.environment_dict,
        pipeline_run=PipelineRun(
            mode=execution_params.mode,
            parent_run_id=execution_params.previous_run_id,
            root_run_id=execution_params.previous_run_id,
            tags=execution_params.execution_metadata.tags,
        ),
    )

    _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan)

    if execution_params.execution_metadata.run_id:
        # If a run_id is provided, use the old get_or_create_run machinery
        run = instance.get_or_create_run(
            _create_pipeline_run(instance, pipeline_def, execution_params)
        )
    else:
        # Otherwise we know we are creating a new run, and we can
        # use the new machinery that persists a pipeline snapshot
        # with the run.
        run = instance.create_run_with_snapshot(
            InstanceCreateRunArgs(
                pipeline_snapshot=pipeline_def.get_pipeline_snapshot(),
                run_id=execution_params.execution_metadata.run_id
                if execution_params.execution_metadata.run_id
                else make_new_run_id(),
                selector=execution_params.selector,
                environment_dict=execution_params.environment_dict,
                mode=execution_params.mode,
                step_keys_to_execute=get_step_keys_to_execute(
                    instance, pipeline_def, execution_params
                )
                or execution_params.step_keys,
                tags=execution_params.execution_metadata.tags,
                status=PipelineRunStatus.NOT_STARTED,
                root_run_id=(
                    execution_params.execution_metadata.root_run_id
                    or execution_params.previous_run_id
                ),
                parent_run_id=(
                    execution_params.execution_metadata.parent_run_id
                    or execution_params.previous_run_id
                ),
            )
        )

    graphene_info.context.execution_manager.execute_pipeline(
        graphene_info.context.get_handle(), pipeline_def, run, instance=instance,
    )

    return graphene_info.schema.type_named(success_type)(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )


@capture_dauphin_error
def start_pipeline_execution_for_created_run(graphene_info, run_id):
    '''This indirection is done on purpose to make the logic in the function
    below re-usable. The parent function is wrapped in @capture_dauphin_error, which makes it
    difficult to do exception handling.
    '''
    return _start_pipeline_execution_for_created_run(graphene_info, run_id)


def _start_pipeline_execution_for_created_run(graphene_info, run_id):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)

    instance = graphene_info.context.instance

    execution_manager_settings = instance.dagit_settings.get('execution_manager')
    if execution_manager_settings and execution_manager_settings.get('disabled'):
        return graphene_info.schema.type_named('StartPipelineExecutionDisabledError')()

    pipeline_run = instance.get_run_by_id(run_id)
    if not pipeline_run:
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)

    pipeline_def = get_pipeline_def_from_selector(graphene_info, pipeline_run.selector)

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

        # TODO: also insert a pipeline init failure event
        # https://github.com/dagster-io/dagster/issues/2385

        return DauphinPipelineConfigValidationInvalid.for_validation_errors(
            pipeline_def, validated_config.errors
        )

    create_execution_plan(
        pipeline_def, pipeline_run.environment_dict, pipeline_run=pipeline_run,
    )

    graphene_info.context.execution_manager.execute_pipeline(
        graphene_info.context.get_handle(), pipeline_def, pipeline_run, instance=instance,
    )

    return graphene_info.schema.type_named('StartPipelineExecutionSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(pipeline_run)
    )
