from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.pipeline import ExecutionSelector

from .fetch_pipelines import get_dagster_pipeline_from_selector
from .utils import capture_dauphin_error


@capture_dauphin_error
def get_partition_sets_or_error(graphene_info, pipeline_name):
    return graphene_info.schema.type_named('PartitionSets')(
        results=_get_partition_sets(graphene_info, pipeline_name)
    )


def _get_partition_sets(graphene_info, pipeline_name):
    partition_sets = get_dagster_partition_sets(graphene_info)

    if pipeline_name:
        pipeline = get_dagster_pipeline_from_selector(
            graphene_info, ExecutionSelector(pipeline_name)
        )
        matching_partition_sets = filter(
            lambda partition_set: partition_set.pipeline_name == pipeline.name, partition_sets
        )
    else:
        matching_partition_sets = partition_sets

    return [
        graphene_info.schema.type_named('PartitionSet')(partition_set)
        for partition_set in matching_partition_sets
    ]


@capture_dauphin_error
def get_partition_set(graphene_info, partition_set_name):
    partition_set = get_dagster_partition_set(graphene_info, partition_set_name)
    return graphene_info.schema.type_named('PartitionSet')(partition_set)


def get_dagster_partition_set(graphene_info, partition_set_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(partition_set_name, 'partition_set_name')

    return graphene_info.context.get_partition_set(partition_set_name)


def get_dagster_partition_sets(graphene_info):
    partitions_handle = graphene_info.context.partitions_handle
    return partitions_handle.get_all_partition_sets()
