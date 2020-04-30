from graphql.execution.base import ResolveInfo

from dagster import check

from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def get_partition_sets_or_error(graphene_info, pipeline_name):
    return graphene_info.schema.type_named('PartitionSets')(
        results=_get_partition_sets(graphene_info, pipeline_name)
    )


def _get_partition_sets(graphene_info, pipeline_name):
    partition_sets = graphene_info.context.get_all_partition_sets()

    if pipeline_name:
        if not graphene_info.context.has_external_pipeline(pipeline_name):
            raise UserFacingGraphQLError(
                graphene_info.schema.type_named('PipelineNotFoundError')(
                    pipeline_name=pipeline_name
                )
            )

        matching_partition_sets = filter(
            lambda partition_set: partition_set.pipeline_name == pipeline_name, partition_sets
        )
    else:
        matching_partition_sets = partition_sets

    return [
        graphene_info.schema.type_named('PartitionSet')(partition_set)
        for partition_set in matching_partition_sets
    ]


@capture_dauphin_error
def get_partition_set(graphene_info, partition_set_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    partition_set = graphene_info.context.get_partition_set(partition_set_name)
    return graphene_info.schema.type_named('PartitionSet')(partition_set)
