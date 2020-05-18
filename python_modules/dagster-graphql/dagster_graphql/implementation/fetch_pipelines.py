from dagster_graphql.implementation.external import (
    get_external_pipeline_or_raise,
    get_full_external_pipeline_or_raise,
)
from dagster_graphql.schema.pipelines import DauphinPipeline, DauphinPipelineSnapshot
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.pipeline import ExecutionSelector

from .utils import UserFacingGraphQLError, capture_dauphin_error


def get_pipeline_snapshot(graphene_info, snapshot_id):
    check.str_param(snapshot_id, 'snapshot_id')
    historical_pipeline = graphene_info.context.instance.get_historical_pipeline(snapshot_id)
    # Check is ok because this is only used for pipelineSnapshot which is for adhoc
    # In fact we should probably delete all the non OrError fields
    check.invariant(historical_pipeline, 'Pipeline fetch failed')
    return DauphinPipelineSnapshot(historical_pipeline)


@capture_dauphin_error
def get_pipeline_snapshot_or_error_from_pipeline_name(graphene_info, pipeline_name):
    check.str_param(pipeline_name, 'pipeline_name')
    return DauphinPipelineSnapshot(
        get_full_external_pipeline_or_raise(graphene_info, pipeline_name)
    )


@capture_dauphin_error
def get_pipeline_snapshot_or_error_from_snapshot_id(graphene_info, snapshot_id):
    check.str_param(snapshot_id, 'snapshot_id')
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
    '''Returns a DauphinPipelineOrError.'''
    return get_dauphin_pipeline_from_selector(graphene_info, selector)


def get_pipeline_or_raise(graphene_info, selector):
    '''Returns a DauphinPipeline or raises a UserFacingGraphQLError if one cannot be retrieved
    from the selector, e.g., the pipeline is not present in the loaded repository.'''
    return get_dauphin_pipeline_from_selector(graphene_info, selector)


def get_pipeline_reference_or_raise(graphene_info, selector):
    '''Returns a DauphinPipelineReference or raises a UserFacingGraphQLError if a pipeline
    reference cannot be retrieved from the selector, e.g, a UserFacingGraphQLError that wraps an
    InvalidSubsetError.'''
    return get_dauphin_pipeline_reference_from_selector(graphene_info, selector)


def get_dauphin_pipeline_reference_from_selector(graphene_info, selector):
    from ..schema.errors import DauphinPipelineNotFoundError, DauphinInvalidSubsetError

    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    try:
        return get_dauphin_pipeline_from_selector(graphene_info, selector)
    except UserFacingGraphQLError as exc:
        if (
            isinstance(exc.dauphin_error, DauphinPipelineNotFoundError)
            or
            # At this time DauphinPipeline represents a potentially subsetted
            # pipeline so if the solids used to subset no longer exist
            # we can't return the correct instance so we fallback to
            # UnknownPipeline
            isinstance(exc.dauphin_error, DauphinInvalidSubsetError)
        ):
            return graphene_info.schema.type_named('UnknownPipeline')(selector.name)

        raise


@capture_dauphin_error
def get_pipelines_or_error(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return get_pipelines_or_raise(graphene_info)


def get_pipelines_or_raise(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    dauphin_pipelines = list(
        map(DauphinPipeline, graphene_info.context.legacy_get_all_external_pipelines())
    )
    return graphene_info.schema.type_named('PipelineConnection')(
        nodes=sorted(dauphin_pipelines, key=lambda pipeline: pipeline.name)
    )


def get_dauphin_pipeline_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    return DauphinPipeline(
        get_external_pipeline_or_raise(graphene_info, selector.name, selector.solid_subset)
    )


def get_reconstructable_pipeline_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    pipeline_name = selector.name

    # for error check of pipeline existence
    get_full_external_pipeline_or_raise(graphene_info, pipeline_name)

    recon_pipeline = graphene_info.context.get_reconstructable_pipeline(pipeline_name)

    if not selector.solid_subset:
        return recon_pipeline

    # for error checking
    get_external_pipeline_or_raise(graphene_info, selector.name, selector.solid_subset)
    return recon_pipeline.subset_for_execution(selector.solid_subset)
