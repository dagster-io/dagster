from dagster import check
from dagster.core.storage.pipeline_run import PipelineRun
from dagster_graphql.implementation.external import (
    get_external_pipeline_or_raise,
    get_full_external_pipeline_or_raise,
)
from dagster_graphql.implementation.utils import PipelineSelector
from dagster_graphql.schema.pipelines import DauphinPipeline, DauphinPipelineSnapshot
from graphql.execution.base import ResolveInfo

from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def get_pipeline_snapshot_or_error_from_pipeline_selector(graphene_info, pipeline_selector):
    check.inst_param(pipeline_selector, "pipeline_selector", PipelineSelector)
    return DauphinPipelineSnapshot(
        get_full_external_pipeline_or_raise(graphene_info, pipeline_selector)
    )


@capture_dauphin_error
def get_pipeline_snapshot_or_error_from_snapshot_id(graphene_info, snapshot_id):
    check.str_param(snapshot_id, "snapshot_id")
    return _get_dauphin_pipeline_snapshot_from_instance(graphene_info.context.instance, snapshot_id)


# extracted this out to test
def _get_dauphin_pipeline_snapshot_from_instance(instance, snapshot_id):
    from dagster_graphql.schema.errors import DauphinPipelineSnapshotNotFoundError

    if not instance.has_pipeline_snapshot(snapshot_id):
        raise UserFacingGraphQLError(DauphinPipelineSnapshotNotFoundError(snapshot_id))

    historical_pipeline = instance.get_historical_pipeline(snapshot_id)

    if not historical_pipeline:
        # Either a temporary error or it has been deleted in the interim
        raise UserFacingGraphQLError(DauphinPipelineSnapshotNotFoundError(snapshot_id))

    return DauphinPipelineSnapshot(historical_pipeline)


@capture_dauphin_error
def get_pipeline_or_error(graphene_info, selector):
    """Returns a DauphinPipelineOrError."""
    return get_dauphin_pipeline_from_selector(graphene_info, selector)


def get_pipeline_or_raise(graphene_info, selector):
    """Returns a DauphinPipeline or raises a UserFacingGraphQLError if one cannot be retrieved
    from the selector, e.g., the pipeline is not present in the loaded repository."""
    return get_dauphin_pipeline_from_selector(graphene_info, selector)


def get_pipeline_reference_or_raise(graphene_info, pipeline_run):
    """Returns a DauphinPipelineReference or raises a UserFacingGraphQLError if a pipeline
    reference cannot be retrieved based on the run, e.g, a UserFacingGraphQLError that wraps an
    InvalidSubsetError."""
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    solid_selection = (
        list(pipeline_run.solids_to_execute) if pipeline_run.solids_to_execute else None
    )

    if pipeline_run.pipeline_snapshot_id is None:
        return graphene_info.schema.type_named("UnknownPipeline")(
            pipeline_run.pipeline_name, solid_selection
        )

    return _get_dauphin_pipeline_snapshot_from_instance(
        graphene_info.context.instance, pipeline_run.pipeline_snapshot_id
    )


def get_dauphin_pipeline_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)

    return DauphinPipeline(get_external_pipeline_or_raise(graphene_info, selector))
