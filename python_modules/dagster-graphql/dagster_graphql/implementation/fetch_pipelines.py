import sys

from dagster_graphql.implementation.context import (
    DagsterGraphQLInProcessRepositoryContext,
    ExternalPipeline,
)
from dagster_graphql.schema.pipelines import DauphinPipeline, DauphinPipelineSnapshot
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.snap import PipelineIndex
from dagster.utils.error import serializable_error_info_from_exc_info

from .utils import UserFacingGraphQLError, capture_dauphin_error


def get_pipeline_snapshot(graphene_info, snapshot_id):
    check.str_param(snapshot_id, 'snapshot_id')
    pipeline_snapshot = graphene_info.context.instance.get_pipeline_snapshot(snapshot_id)
    return DauphinPipelineSnapshot(PipelineIndex(pipeline_snapshot))


@capture_dauphin_error
def get_pipeline_snapshot_or_error_from_pipeline_name(graphene_info, pipeline_name):
    check.str_param(pipeline_name, 'pipeline_name')
    repository_index = graphene_info.context.get_repository_index()
    if not repository_index.has_pipeline(pipeline_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=pipeline_name)
        )
    return DauphinPipelineSnapshot(repository_index.get_pipeline_index(pipeline_name))


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

    pipeline_name = selector.name

    if not graphene_info.context.has_external_pipeline(pipeline_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=pipeline_name)
        )

    external_pipeline = graphene_info.context.get_external_pipeline(pipeline_name)

    if not selector.solid_subset:
        return DauphinPipeline(external_pipeline)

    _check_for_invalid_subset(external_pipeline, selector.solid_subset)

    return DauphinPipeline(
        graphene_info.context.get_external_pipeline_subset(pipeline_name, selector.solid_subset)
    )


def _check_for_invalid_subset(external_pipeline, solid_subset):
    check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
    check.list_param(solid_subset, 'solid_subset', of_type=str)

    for solid_name in solid_subset:
        if not external_pipeline.has_solid_invocation(solid_name):
            from dagster_graphql.schema.errors import DauphinInvalidSubsetError

            raise UserFacingGraphQLError(
                DauphinInvalidSubsetError(
                    message='Solid "{solid_name}" does not exist in "{pipeline_name}"'.format(
                        solid_name=solid_name, pipeline_name=external_pipeline.name
                    ),
                    pipeline=DauphinPipeline(external_pipeline),
                )
            )


def get_pipeline_def_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    check.invariant(
        isinstance(graphene_info.context, DagsterGraphQLInProcessRepositoryContext),
        'Can only get definition objects in process',
    )

    pipeline_name = selector.name

    if not graphene_info.context.has_external_pipeline(pipeline_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=pipeline_name)
        )

    orig_pipeline = graphene_info.context.get_pipeline(pipeline_name)

    if not selector.solid_subset:
        return orig_pipeline

    _check_for_invalid_subset(
        ExternalPipeline.from_pipeline_def(orig_pipeline), selector.solid_subset
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
