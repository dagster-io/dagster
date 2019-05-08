import sys

from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from dagster.core.execution.api import ExecutionSelector

from dagster.utils.error import serializable_error_info_from_exc_info

from .either import EitherError, EitherValue


def get_pipeline(graphene_info, selector):
    return _get_pipeline(graphene_info, selector).value()


def get_pipeline_or_raise(graphene_info, selector):
    return _get_pipeline(graphene_info, selector).value_or_raise()


def get_pipelines(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return _get_pipelines(graphene_info).value()


def get_pipelines_or_raise(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return _get_pipelines(graphene_info).value_or_raise()


def _get_pipeline(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    return _pipeline_or_error_from_container(graphene_info, selector)


def _get_pipelines(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)

    def process_pipelines(repository):
        try:
            pipeline_instances = []
            for pipeline_def in repository.get_all_pipelines():
                pipeline_instances.append(graphene_info.schema.type_named('Pipeline')(pipeline_def))
            return graphene_info.schema.type_named('PipelineConnection')(
                nodes=sorted(pipeline_instances, key=lambda pipeline: pipeline.name)
            )
        except DagsterInvalidDefinitionError:
            return EitherError(
                graphene_info.schema.type_named('InvalidDefinitionError')(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )
        except Exception:  # pylint: disable=broad-except
            return EitherError(
                graphene_info.schema.type_named('PythonError')(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

    repository_or_error = _repository_or_error_from_container(graphene_info)
    return repository_or_error.chain(process_pipelines)


def _pipeline_or_error_from_container(graphene_info, selector):
    return _repository_or_error_from_container(graphene_info).chain(
        lambda repository: _pipeline_or_error_from_repository(graphene_info, repository, selector)
    )


def _repository_or_error_from_container(graphene_info):
    container = graphene_info.context.repository_container
    error = container.error
    if error is not None:
        return EitherError(
            graphene_info.schema.type_named('PythonError')(
                serializable_error_info_from_exc_info(error)
            )
        )
    try:
        return EitherValue(container.repository)
    except Exception:  # pylint: disable=broad-except
        return EitherError(
            graphene_info.schema.type_named('PythonError')(
                serializable_error_info_from_exc_info(sys.exc_info())
            )
        )


def _pipeline_or_error_from_repository(graphene_info, repository, selector):
    if not repository.has_pipeline(selector.name):
        return EitherError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=selector.name)
        )
    else:
        orig_pipeline = repository.get_pipeline(selector.name)
        if selector.solid_subset:
            for solid_name in selector.solid_subset:
                if not orig_pipeline.has_solid_named(solid_name):
                    return EitherError(
                        graphene_info.schema.type_named('SolidNotFoundError')(solid_name=solid_name)
                    )
        pipeline = orig_pipeline.build_sub_pipeline(selector.solid_subset)

        return EitherValue(graphene_info.schema.type_named('Pipeline')(pipeline))


def get_pipeline_presets(graphene_info, pipeline_name):
    repo = graphene_info.context.repository_container.repository

    return [
        graphene_info.schema.type_named('PipelinePreset')(preset)
        for preset in repo.get_presets_for_pipeline(pipeline_name).values()
    ]
