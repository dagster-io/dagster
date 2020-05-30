from __future__ import absolute_import

from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid
from graphql.execution.base import ResolveInfo

from dagster import DagsterInvalidConfigError, check
from dagster.config.validate import validate_config_from_snap
from dagster.core.events import EngineEventData
from dagster.core.execution.api import execute_run
from dagster.utils.error import SerializableErrorInfo
from dagster.utils.hosted_user_process import pipeline_def_from_pipeline_handle

from ..external import legacy_get_external_pipeline_or_raise
from ..utils import ExecutionParams, capture_dauphin_error
from .launch_execution import do_launch


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

    check.invariant(
        graphene_info.context.instance.run_launcher,
        'Should always be true. '
        'The reign of the execution manager is over. The time of the run launcher has come.',
    )

    run = do_launch(graphene_info, execution_params, is_reexecuted)

    return graphene_info.schema.type_named('StartPipelineRunSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )


@capture_dauphin_error
def start_pipeline_execution_for_created_run(graphene_info, run_id):
    '''This indirection is done on purpose to make the logic in the function
    below re-usable. The parent function is wrapped in @capture_dauphin_error, which makes it
    difficult to do exception handling.
    '''
    return _synchronously_execute_run_within_hosted_user_process(graphene_info, run_id)


def _synchronously_execute_run_within_hosted_user_process(graphene_info, run_id):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)

    instance = graphene_info.context.instance

    pipeline_run = instance.get_run_by_id(run_id)
    if not pipeline_run:
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)

    external_pipeline = legacy_get_external_pipeline_or_raise(
        graphene_info, pipeline_run.pipeline_name, pipeline_run.solid_subset
    )

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

    pipeline_def = pipeline_def_from_pipeline_handle(external_pipeline.handle)
    execute_run(pipeline_def, pipeline_run, instance)

    return graphene_info.schema.type_named('StartPipelineRunSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(pipeline_run)
    )
