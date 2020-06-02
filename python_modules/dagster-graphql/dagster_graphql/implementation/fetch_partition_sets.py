from graphql.execution.base import ResolveInfo

from dagster import check

from .external import get_full_external_pipeline_or_raise
from .utils import capture_dauphin_error, legacy_pipeline_selector


@capture_dauphin_error
def get_partition_sets_or_error(graphene_info, pipeline_name):
    return graphene_info.schema.type_named('PartitionSets')(
        results=_get_partition_sets(graphene_info, pipeline_name)
    )


def _get_partition_sets(graphene_info, pipeline_name):
    external_partition_sets = (
        graphene_info.context.legacy_external_repository.get_external_partition_sets()
    )
    if pipeline_name:

        external_pipeline = get_full_external_pipeline_or_raise(
            graphene_info,
            legacy_pipeline_selector(graphene_info.context, pipeline_name, solid_selection=None),
        )

        matching_partition_sets = filter(
            lambda partition_set: partition_set.pipeline_name == external_pipeline.name,
            external_partition_sets,
        )
    else:
        matching_partition_sets = external_partition_sets

    return [
        graphene_info.schema.type_named('PartitionSet')(
            external_partition_set=external_partition_set,
            partition_set_def=graphene_info.context.legacy_get_repository_definition().get_partition_set_def(
                external_partition_set.name
            ),
        )
        for external_partition_set in sorted(
            matching_partition_sets,
            key=lambda partition_set: (
                partition_set.pipeline_name,
                partition_set.mode,
                partition_set.name,
            ),
        )
    ]


@capture_dauphin_error
def get_partition_set(graphene_info, partition_set_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    partition_sets = graphene_info.context.legacy_external_repository.get_external_partition_sets()
    for partition_set in partition_sets:
        if partition_set.name == partition_set_name:
            return graphene_info.schema.type_named('PartitionSet')(
                external_partition_set=partition_set,
                partition_set_def=graphene_info.context.legacy_get_repository_definition().get_partition_set_def(
                    partition_set_name
                ),
            )

    return graphene_info.schema.type_named('PartitionSetNotFoundError')(partition_set_name)
