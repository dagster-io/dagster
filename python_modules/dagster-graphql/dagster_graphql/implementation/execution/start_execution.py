from __future__ import absolute_import

from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid
from graphql.execution.base import ResolveInfo

from dagster import DagsterInvalidConfigError, check
from dagster.config.validate import validate_config
from dagster.core.definitions.environment_schema import create_environment_schema
from dagster.core.errors import DagsterRunConflict
from dagster.core.events import EngineEventData
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts
from dagster.utils.error import SerializableErrorInfo

from ..external import (
    ensure_valid_config,
    get_execution_plan_index_or_raise,
    get_external_pipeline_subset_or_raise,
)
from ..fetch_pipelines import get_pipeline_def_from_selector
from ..utils import ExecutionMetadata, ExecutionParams, capture_dauphin_error
from .utils import get_step_keys_to_execute


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

    instance = graphene_info.context.instance
    execution_manager_settings = instance.dagit_settings.get('execution_manager')
    if execution_manager_settings and execution_manager_settings.get('disabled'):
        return graphene_info.schema.type_named('StartPipelineRunDisabledError')()

    pipeline_def_delete_me = get_pipeline_def_from_selector(
        graphene_info, execution_params.selector
    )

    external_pipeline = get_external_pipeline_subset_or_raise(
        graphene_info, execution_params.selector.name, execution_params.selector.solid_subset
    )

    ensure_valid_config(external_pipeline, execution_params.mode, execution_params.environment_dict)

    # TODO rename function and it always returns something so "or" is superfluous
    step_keys_to_execute = (
        get_step_keys_to_execute(instance, pipeline_def_delete_me, execution_params)
        or execution_params.step_keys
    )

    execution_plan_index = get_execution_plan_index_or_raise(
        graphene_info,
        external_pipeline,
        mode=execution_params.mode,
        environment_dict=execution_params.environment_dict,
        step_keys_to_execute=step_keys_to_execute,
    )

    try:
        pipeline_run = instance.create_run(
            pipeline_name=external_pipeline.name,
            run_id=execution_params.execution_metadata.run_id
            if execution_params.execution_metadata.run_id
            else make_new_run_id(),
            solid_subset=execution_params.selector.solid_subset
            if execution_params.selector
            else None,
            environment_dict=execution_params.environment_dict,
            mode=execution_params.mode,
            step_keys_to_execute=step_keys_to_execute,
            tags=merge_dicts(external_pipeline.tags, execution_params.execution_metadata.tags),
            status=PipelineRunStatus.NOT_STARTED,
            root_run_id=execution_params.execution_metadata.root_run_id,
            parent_run_id=execution_params.execution_metadata.parent_run_id,
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=execution_plan_index.execution_plan_snapshot,
        )

    except DagsterRunConflict as exc:
        return graphene_info.schema.type_named('PipelineRunConflict')(exc)

    graphene_info.context.execute_pipeline(external_pipeline, pipeline_run)

    return graphene_info.schema.type_named('StartPipelineRunSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(pipeline_run)
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
        return graphene_info.schema.type_named('StartPipelineRunDisabledError')()

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

        instance.report_run_failed(pipeline_run)

        return DauphinPipelineConfigValidationInvalid.for_validation_errors(
            pipeline_def.get_pipeline_index(), validated_config.errors
        )

    graphene_info.context.execution_manager.execute_pipeline(
        graphene_info.context.get_handle(), pipeline_def, pipeline_run, instance=instance,
    )

    return graphene_info.schema.type_named('StartPipelineRunSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(pipeline_run)
    )
