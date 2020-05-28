from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.partition import PartitionScheduleDefinition

from .external import get_full_external_pipeline_or_raise
from .utils import PipelineSelector, capture_dauphin_error


@capture_dauphin_error
def get_partition_sets_or_error(graphene_info, pipeline_name):
    return graphene_info.schema.type_named('PartitionSets')(
        results=_get_partition_sets(graphene_info, pipeline_name)
    )


def _partitions_from_repo(repo_def):
    return repo_def.partition_set_defs + [
        schedule_def.get_partition_set()
        for schedule_def in repo_def.schedule_defs
        if isinstance(schedule_def, PartitionScheduleDefinition)
    ]


def _get_partition_sets(graphene_info, pipeline_name):
    partition_sets = _partitions_from_repo(graphene_info.context.legacy_get_repository_definition())

    if pipeline_name:

        external_pipeline = get_full_external_pipeline_or_raise(
            graphene_info,
            PipelineSelector.legacy(graphene_info.context, pipeline_name, solid_subset=None),
        )

        matching_partition_sets = filter(
            lambda partition_set: partition_set.pipeline_name == external_pipeline.name,
            partition_sets,
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
    partition_sets = _partitions_from_repo(graphene_info.context.legacy_get_repository_definition())
    for partition_set in partition_sets:
        if partition_set.name == partition_set_name:
            return graphene_info.schema.type_named('PartitionSet')(partition_set)

    return graphene_info.schema.type_named('PartitionSetNotFoundError')(partition_set_name)
