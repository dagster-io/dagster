from dagster_graphql.schema.runtime_types import to_dauphin_runtime_type

from dagster.core.definitions.pipeline import ExecutionSelector

from .fetch_pipelines import get_dagster_pipeline_from_selector
from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def get_runtime_type(graphene_info, pipeline_name, type_name):
    pipeline = get_dagster_pipeline_from_selector(graphene_info, ExecutionSelector(pipeline_name))

    if not pipeline.has_runtime_type(type_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('RuntimeTypeNotFoundError')(
                pipeline=pipeline, runtime_type_name=type_name
            )
        )

    return to_dauphin_runtime_type(pipeline.runtime_type_named(type_name))
