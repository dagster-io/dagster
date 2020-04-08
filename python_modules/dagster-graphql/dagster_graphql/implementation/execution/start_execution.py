from __future__ import absolute_import

from dagster_graphql.client.util import execution_params_from_pipeline_run
from graphql.execution.base import ResolveInfo

from dagster import RunConfig, check
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import InstanceCreateRunArgs
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.utils import make_new_run_id

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
        graphene_info,
        pipeline_def,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
    )

    execution_plan = create_execution_plan(
        pipeline_def,
        execution_params.environment_dict,
        run_config=RunConfig(
            mode=execution_params.mode,
            previous_run_id=execution_params.previous_run_id,
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
    return _start_pipeline_execution_for_created_run(graphene_info, run_id)


def _start_pipeline_execution_for_created_run(graphene_info, run_id):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)

    instance = graphene_info.context.instance

    execution_manager_settings = instance.dagit_settings.get('execution_manager')
    if execution_manager_settings and execution_manager_settings.get('disabled'):
        return graphene_info.schema.type_named('StartPipelineExecutionDisabledError')()

    run = instance.get_run_by_id(run_id)
    if not run:
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)

    pipeline_def = get_pipeline_def_from_selector(graphene_info, run.selector)

    get_validated_config(
        graphene_info, pipeline_def, environment_dict=run.environment_dict, mode=run.mode,
    )

    execution_plan = create_execution_plan(
        pipeline_def,
        run.environment_dict,
        run_config=RunConfig(mode=run.mode, previous_run_id=run.previous_run_id, tags=run.tags,),
    )

    execution_params = execution_params_from_pipeline_run(run)

    _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan)

    graphene_info.context.execution_manager.execute_pipeline(
        graphene_info.context.get_handle(), pipeline_def, run, instance=instance,
    )

    return graphene_info.schema.type_named('StartPipelineExecutionSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )
