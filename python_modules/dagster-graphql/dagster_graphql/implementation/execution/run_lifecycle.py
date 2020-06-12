from collections import namedtuple

from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.config.validate import validate_config_from_snap
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.events import EngineEventData
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts
from dagster.utils.error import SerializableErrorInfo

from ..external import (
    ensure_valid_config,
    get_external_execution_plan_or_raise,
    get_external_pipeline_or_raise,
)
from ..resume_retry import compute_step_keys_to_execute
from ..utils import PipelineSelector


def create_valid_pipeline_run(graphene_info, external_pipeline, execution_params):
    ensure_valid_config(external_pipeline, execution_params.mode, execution_params.run_config)

    step_keys_to_execute = compute_step_keys_to_execute(
        graphene_info, external_pipeline, execution_params
    )

    external_execution_plan = get_external_execution_plan_or_raise(
        graphene_info=graphene_info,
        external_pipeline=external_pipeline,
        mode=execution_params.mode,
        run_config=execution_params.run_config,
        step_keys_to_execute=step_keys_to_execute,
    )

    return graphene_info.context.instance.create_run(
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        pipeline_name=execution_params.selector.pipeline_name,
        run_id=execution_params.execution_metadata.run_id
        if execution_params.execution_metadata.run_id
        else make_new_run_id(),
        solids_to_execute=frozenset(execution_params.selector.solid_selection)
        if execution_params.selector.solid_selection
        else None,
        run_config=execution_params.run_config,
        mode=execution_params.mode,
        step_keys_to_execute=step_keys_to_execute,
        tags=merge_dicts(external_pipeline.tags, execution_params.execution_metadata.tags),
        root_run_id=execution_params.execution_metadata.root_run_id,
        parent_run_id=execution_params.execution_metadata.parent_run_id,
        status=PipelineRunStatus.NOT_STARTED,
    )


RunExecutionInfo = namedtuple('_RunExecutionInfo', 'external_pipeline pipeline_run')


def get_run_execution_info_for_created_run_or_error(
    graphene_info, repository_location_name, repository_name, run_id
):
    '''
    Previously created run could either be created in a different process *or*
    during the launchScheduledRun call where we want to have a record of
    a run the was created but have invalid configuration
    '''
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(repository_location_name, 'repository_location_name')
    check.str_param(repository_name, 'repository_name')
    check.str_param(run_id, 'run_id')

    instance = graphene_info.context.instance

    pipeline_run = instance.get_run_by_id(run_id)
    if not pipeline_run:
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)

    external_pipeline = get_external_pipeline_or_raise(
        graphene_info,
        PipelineSelector(
            location_name=repository_location_name,
            repository_name=repository_name,
            pipeline_name=pipeline_run.pipeline_name,
            solid_selection=list(pipeline_run.solids_to_execute)
            if pipeline_run.solids_to_execute
            else None,
        ),
    )

    validated_config = validate_config_from_snap(
        external_pipeline.config_schema_snapshot,
        external_pipeline.root_config_key_for_mode(pipeline_run.mode),
        pipeline_run.run_config,
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
            pipeline_run.run_config,
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

    return RunExecutionInfo(external_pipeline, pipeline_run)
