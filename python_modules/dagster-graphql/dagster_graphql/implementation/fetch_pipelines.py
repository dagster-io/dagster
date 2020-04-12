import sys

from dagster_graphql.implementation.context import DagsterGraphQLContext
from dagster_graphql.schema.pipelines import DauphinPipeline, DauphinPipelineSnapshot
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.snap.pipeline_snapshot import PipelineIndex
from dagster.utils.error import serializable_error_info_from_exc_info

from .utils import UserFacingGraphQLError, capture_dauphin_error


def get_pipeline_snapshot(graphene_info, snapshot_id):
    check.str_param(snapshot_id, 'snapshot_id')
    pipeline_snapshot = graphene_info.context.instance.get_pipeline_snapshot(snapshot_id)
    return DauphinPipelineSnapshot(PipelineIndex(pipeline_snapshot))


@capture_dauphin_error
def get_pipeline_snapshot_or_error(graphene_info, snapshot_id):
    check.str_param(snapshot_id, 'snapshot_id')
    instance = graphene_info.context.instance
    return _get_dauphin_pipeline_snapshot_from_instance(instance, snapshot_id)


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
    return _get_pipelines(graphene_info)


def get_pipelines_or_raise(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return _get_pipelines(graphene_info)


def _get_pipelines(graphene_info):
    dauphin_pipelines = get_dauphin_pipelines(graphene_info)
    return graphene_info.schema.type_named('PipelineConnection')(
        nodes=sorted(dauphin_pipelines, key=lambda pipeline: pipeline.name)
    )


def get_dauphin_pipelines(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    repository_index = graphene_info.context.get_repository_index()
    return [
        get_dauphin_pipeline_from_pipeline_index(graphene_info, pipeline_index)
        for pipeline_index in repository_index.get_pipeline_indices()
    ]


def get_dauphin_pipeline_from_pipeline_index(graphene_info, pipeline_index):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
    if isinstance(graphene_info.context, DagsterGraphQLContext):
        pipeline = get_pipeline_definition(graphene_info, pipeline_index.pipeline_snapshot.name)
        return DauphinPipeline(pipeline_index, presets=pipeline.get_presets())
    return DauphinPipeline(pipeline_index)


def get_dauphin_pipeline_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    if isinstance(graphene_info.context, DagsterGraphQLContext):
        pipeline_definition = get_pipeline_def_from_selector(graphene_info, selector)
        return DauphinPipeline.from_pipeline_def(pipeline_definition)

    # TODO: Support solid sub selection.
    check.invariant(
        not selector.solid_subset,
        desc="DagsterSnapshotGraphQLContext doesn't support pipeline sub-selection.",
    )

    repository_index = graphene_info.context.get_repository_index()
    if not repository_index.has_pipeline_index(selector.name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=selector.name)
        )
    return DauphinPipeline(repository_index.get_pipeline_index(selector.name))


def get_pipeline_def_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    if not selector.solid_subset:
        return get_pipeline_definition(graphene_info, selector.name)
    return get_solid_subset_pipeline_definition(graphene_info, selector)


def get_pipeline_definition(graphene_info, pipeline_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    repository = graphene_info.context.get_repository()
    if not repository.has_pipeline(pipeline_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=pipeline_name)
        )
    return graphene_info.context.get_pipeline(pipeline_name)


def get_solid_subset_pipeline_definition(graphene_info, selector):
    orig_pipeline = get_pipeline_definition(graphene_info, selector.name)
    for solid_name in selector.solid_subset:
        if not orig_pipeline.has_solid_named(solid_name):
            raise UserFacingGraphQLError(
                graphene_info.schema.type_named('InvalidSubsetError')(
                    message='Solid "{solid_name}" does not exist in "{pipeline_name}"'.format(
                        solid_name=solid_name, pipeline_name=selector.name
                    ),
                    pipeline=graphene_info.schema.type_named('Pipeline').from_pipeline_def(
                        orig_pipeline
                    ),
                )
            )
    try:
        return orig_pipeline.build_sub_pipeline(selector.solid_subset)
    except DagsterInvalidDefinitionError:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('InvalidSubsetError')(
                message=serializable_error_info_from_exc_info(sys.exc_info()).message,
                pipeline=graphene_info.schema.type_named('Pipeline').from_pipeline_def(
                    orig_pipeline
                ),
            )
        )
