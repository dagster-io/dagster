from dagster_graphql.implementation.context import DagsterGraphQLInProcessRepositoryContext
from dagster_graphql.implementation.external import (
    get_external_pipeline_or_raise,
    get_external_pipeline_subset_or_raise,
)
from dagster_graphql.schema.pipelines import DauphinPipeline, DauphinPipelineSnapshot
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.snap import PipelineIndex

from .utils import UserFacingGraphQLError, capture_dauphin_error


def get_pipeline_snapshot(graphene_info, snapshot_id):
    check.str_param(snapshot_id, 'snapshot_id')
    pipeline_snapshot = graphene_info.context.instance.get_pipeline_snapshot(snapshot_id)
    return DauphinPipelineSnapshot(PipelineIndex(pipeline_snapshot))


@capture_dauphin_error
def get_pipeline_snapshot_or_error_from_pipeline_name(graphene_info, pipeline_name):
    check.str_param(pipeline_name, 'pipeline_name')
    return DauphinPipelineSnapshot(
        get_external_pipeline_or_raise(graphene_info, pipeline_name).pipeline_index
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

    pipeline_snapshot = instance.get_pipeline_snapshot(snapshot_id)

    if not pipeline_snapshot:
        # Either a temporary error or it has been deleted in the interim
        raise UserFacingGraphQLError(DauphinPipelineSnapshotNotFoundError(snapshot_id))

    return DauphinPipelineSnapshot(PipelineIndex(pipeline_snapshot))


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
        map(DauphinPipeline, graphene_info.context.get_all_external_pipelines())
    )
    return graphene_info.schema.type_named('PipelineConnection')(
        nodes=sorted(dauphin_pipelines, key=lambda pipeline: pipeline.name)
    )


def get_dauphin_pipeline_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    if not isinstance(graphene_info.context, DagsterGraphQLInProcessRepositoryContext):
        # TODO: Support solid sub selection.
        check.invariant(
            not selector.solid_subset,
            desc="DagsterGraphQLOutOfProcessRepositoryContext doesn't support pipeline sub-selection.",
        )

    return DauphinPipeline(
        get_external_pipeline_subset_or_raise(graphene_info, selector.name, selector.solid_subset)
    )


def get_pipeline_def_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    check.invariant(
        isinstance(graphene_info.context, DagsterGraphQLInProcessRepositoryContext),
        'Can only get definition objects in process',
    )

    pipeline_name = selector.name

    # for error check of pipeline existence
    get_external_pipeline_or_raise(graphene_info, pipeline_name)

    orig_pipeline_def = graphene_info.context.get_pipeline(pipeline_name)

    if not selector.solid_subset:
        return orig_pipeline_def

    # for error checking
    get_external_pipeline_subset_or_raise(graphene_info, selector.name, selector.solid_subset)
    return orig_pipeline_def.build_sub_pipeline(selector.solid_subset)
