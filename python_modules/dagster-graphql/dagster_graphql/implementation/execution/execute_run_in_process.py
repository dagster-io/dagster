from collections import namedtuple

from dagster_graphql.schema.errors import DauphinPipelineConfigValidationInvalid
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.config.validate import validate_config_from_snap
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.events import EngineEventData
from dagster.core.execution.api import execute_run
from dagster.core.host_representation.handle import IN_PROCESS_NAME
from dagster.utils.error import SerializableErrorInfo
from dagster.utils.hosted_user_process import recon_pipeline_from_origin

from ..external import get_external_pipeline_or_raise
from ..utils import PipelineSelector, capture_dauphin_error


@capture_dauphin_error
def execute_run_in_graphql_process(
    graphene_info, repository_location_name, repository_name, run_id
):
    """This indirection is done on purpose to make the logic in the function
    below re-usable. The parent function is wrapped in @capture_dauphin_error, which makes it
    difficult to do exception handling.
    """
    return _synchronously_execute_run_within_hosted_user_process(
        graphene_info, repository_location_name, repository_name, run_id
    )


RunExecutionInfo = namedtuple("_RunExecutionInfo", "external_pipeline pipeline_run")


# Welcome, to Greasy Hack Park
#
# Until https://github.com/dagster-io/dagster/issues/2608 is resolved
# the launch_scheduled_execution may be going from user process requesting in to
# a host process, which means it will be incorrectly requesting repository_location_name
# as "<<in_process>>". Below we attempt to workaround this by matching on the other
# identifiers, and replacing repository_location_name if there is a single match.
def _repository_location_name_workaround(
    context, respository_location_name, repository_name, pipeline_name
):
    if respository_location_name != IN_PROCESS_NAME:
        return respository_location_name

    match = None
    for location in context.repository_locations:
        if location.has_repository(repository_name):
            repo = location.get_repository(repository_name)
            if repo.has_pipeline(pipeline_name) and match is None:
                match = location.name
            elif repo.has_pipeline(pipeline_name) and match is not None:
                # multiple matches, return original
                return respository_location_name
    if match:
        return match

    return respository_location_name


def _get_selector_with_workaround(
    context, respository_location_name, repository_name, pipeline_run
):
    return PipelineSelector(
        location_name=_repository_location_name_workaround(
            context, respository_location_name, repository_name, pipeline_run.pipeline_name
        ),
        repository_name=repository_name,
        pipeline_name=pipeline_run.pipeline_name,
        solid_selection=list(pipeline_run.solids_to_execute)
        if pipeline_run.solids_to_execute
        else None,
    )


def get_run_execution_info_for_created_run_or_error(
    graphene_info, repository_location_name, repository_name, run_id
):
    """
    Previously created run could either be created in a different process *or*
    during the launchScheduledRun call where we want to have a record of
    a run the was created but have invalid configuration
    """
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.str_param(repository_location_name, "repository_location_name")
    check.str_param(repository_name, "repository_name")
    check.str_param(run_id, "run_id")

    instance = graphene_info.context.instance

    pipeline_run = instance.get_run_by_id(run_id)
    if not pipeline_run:
        return graphene_info.schema.type_named("PipelineRunNotFoundError")(run_id)

    external_pipeline = get_external_pipeline_or_raise(
        graphene_info,
        _get_selector_with_workaround(
            graphene_info.context, repository_location_name, repository_name, pipeline_run
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
            "Error in config for pipeline {}".format(external_pipeline.name),
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


def _synchronously_execute_run_within_hosted_user_process(
    graphene_info, repository_location_name, repository_name, run_id,
):
    run_info_or_error = get_run_execution_info_for_created_run_or_error(
        graphene_info, repository_location_name, repository_name, run_id
    )

    if not isinstance(run_info_or_error, RunExecutionInfo):
        # if it is not a success the return value is the dauphin error
        return run_info_or_error

    external_pipeline, pipeline_run = run_info_or_error
    recon_pipeline = recon_pipeline_from_origin(external_pipeline.get_origin())
    execute_run(recon_pipeline, pipeline_run, graphene_info.context.instance)
    return graphene_info.schema.type_named("ExecuteRunInProcessSuccess")(
        run=graphene_info.schema.type_named("PipelineRun")(pipeline_run)
    )
