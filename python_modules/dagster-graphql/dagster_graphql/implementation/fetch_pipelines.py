import sys

from dagster_graphql.schema.pipelines import DauphinPipeline
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils.error import serializable_error_info_from_exc_info

from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def get_pipeline_or_error(graphene_info, selector):
    '''Returns a DauphinPipelineOrError.'''
    return DauphinPipeline(get_pipeline_def_from_selector(graphene_info, selector))


def get_pipeline_or_raise(graphene_info, selector):
    '''Returns a DauphinPipeline or raises a UserFacingGraphQLError if one cannot be retrieved
    from the selector, e.g., the pipeline is not present in the loaded repository.'''
    return DauphinPipeline(get_pipeline_def_from_selector(graphene_info, selector))


def get_pipeline_reference_or_raise(graphene_info, selector):
    '''Returns a DauphinPipelineReference or raises a UserFacingGraphQLError if a pipeline
    reference cannot be retrieved from the selector, e.g, a UserFacingGraphQLError that wraps an
    InvalidSubsetError.'''
    return get_dauphin_pipeline_reference_from_selector(graphene_info, selector)


@capture_dauphin_error
def get_pipelines_or_error(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return _get_pipelines(graphene_info)


def get_pipelines_or_raise(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return _get_pipelines(graphene_info)


def _get_pipelines(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)

    repository = graphene_info.context.get_repository()

    pipeline_instances = []
    for pipeline_def in repository.get_all_pipelines():
        pipeline_instances.append(graphene_info.schema.type_named('Pipeline')(pipeline_def))
    return graphene_info.schema.type_named('PipelineConnection')(
        nodes=sorted(pipeline_instances, key=lambda pipeline: pipeline.name)
    )


def get_pipeline_def_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    repository = graphene_info.context.get_repository()
    if not repository.has_pipeline(selector.name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=selector.name)
        )

    orig_pipeline = graphene_info.context.get_pipeline(selector.name)
    if not selector.solid_subset:
        return orig_pipeline
    else:
        for solid_name in selector.solid_subset:
            if not orig_pipeline.has_solid_named(solid_name):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidSubsetError')(
                        message='Solid "{solid_name}" does not exist in "{pipeline_name}"'.format(
                            solid_name=solid_name, pipeline_name=selector.name
                        ),
                        pipeline=graphene_info.schema.type_named('Pipeline')(orig_pipeline),
                    )
                )
        try:
            return orig_pipeline.build_sub_pipeline(selector.solid_subset)
        except DagsterInvalidDefinitionError:
            raise UserFacingGraphQLError(
                graphene_info.schema.type_named('InvalidSubsetError')(
                    message=serializable_error_info_from_exc_info(sys.exc_info()).message,
                    pipeline=graphene_info.schema.type_named('Pipeline')(orig_pipeline),
                )
            )


def get_dauphin_pipeline_reference_from_selector(graphene_info, selector):
    from ..schema.errors import DauphinPipelineNotFoundError, DauphinInvalidSubsetError

    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    try:
        return graphene_info.schema.type_named('Pipeline')(
            get_pipeline_def_from_selector(graphene_info, selector)
        )

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
