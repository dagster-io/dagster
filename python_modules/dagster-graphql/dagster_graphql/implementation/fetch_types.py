from dagster_graphql.schema.runtime_types import to_dauphin_dagster_type

from dagster.core.definitions.pipeline import ExecutionSelector

from .fetch_pipelines import get_dauphin_pipeline_from_selector
from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def get_dagster_type(graphene_info, pipeline_name, type_name):
    dauphin_pipeline = get_dauphin_pipeline_from_selector(
        graphene_info, ExecutionSelector(pipeline_name)
    )
    pipeline_index = dauphin_pipeline.get_pipeline_index()

    if not pipeline_index.has_dagster_type_name(type_name):
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('RuntimeTypeNotFoundError')(
                pipeline=dauphin_pipeline, runtime_type_name=type_name
            )
        )

    return to_dauphin_dagster_type(
        pipeline_index.pipeline_snapshot, pipeline_index.get_dagster_type_from_name(type_name).key,
    )
