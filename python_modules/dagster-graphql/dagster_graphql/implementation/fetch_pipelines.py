import sys

from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.api import ExecutionSelector
from dagster.utils.error import serializable_error_info_from_exc_info

from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def get_pipeline_or_error(graphene_info, selector):
    return get_dauphin_pipeline_from_selector(graphene_info, selector)


def get_pipeline_or_raise(graphene_info, selector):
    return get_dauphin_pipeline_from_selector(graphene_info, selector)


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

    try:
        pipeline_instances = []
        for pipeline_def in repository.get_all_pipelines():
            pipeline_instances.append(graphene_info.schema.type_named('Pipeline')(pipeline_def))
        return graphene_info.schema.type_named('PipelineConnection')(
            nodes=sorted(pipeline_instances, key=lambda pipeline: pipeline.name)
        )
    except DagsterInvalidDefinitionError:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('InvalidDefinitionError')(
                serializable_error_info_from_exc_info(sys.exc_info())
            )
        )
    except Exception:  # pylint: disable=broad-except
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PythonError')(
                serializable_error_info_from_exc_info(sys.exc_info())
            )
        )


def get_dagster_pipeline_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    repository = graphene_info.context.get_repository()
    if not repository.has_pipeline(selector.name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=selector.name)
        )

    orig_pipeline = graphene_info.context.get_pipeline(selector.name)
    if selector.solid_subset:
        for solid_name in selector.solid_subset:
            if not orig_pipeline.has_solid_named(solid_name):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('SolidNotFoundError')(solid_name=solid_name)
                )
    return orig_pipeline.build_sub_pipeline(selector.solid_subset)


def get_dauphin_pipeline_from_selector(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    return graphene_info.schema.type_named('Pipeline')(
        get_dagster_pipeline_from_selector(graphene_info, selector)
    )
