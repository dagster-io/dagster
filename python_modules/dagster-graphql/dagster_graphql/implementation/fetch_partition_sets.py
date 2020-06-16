from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.api.snapshot_partition import sync_get_external_partition
from dagster.core.host_representation import (
    ExternalPartitionSet,
    RepositoryHandle,
    RepositorySelector,
)

from .utils import capture_dauphin_error


def get_partition_sets_or_error(graphene_info, repository_selector, pipeline_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(repository_selector, 'repository_selector', RepositorySelector)
    check.str_param(pipeline_name, 'pipeline_name')
    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    partition_sets = [
        partition_set
        for partition_set in repository.get_external_partition_sets()
        if partition_set.pipeline_name == pipeline_name
    ]

    return graphene_info.schema.type_named('PartitionSets')(
        results=[
            graphene_info.schema.type_named('PartitionSet')(
                external_repository_handle=repository.handle, external_partition_set=partition_set,
            )
            for partition_set in sorted(
                partition_sets,
                key=lambda partition_set: (
                    partition_set.pipeline_name,
                    partition_set.mode,
                    partition_set.name,
                ),
            )
        ]
    )


@capture_dauphin_error
def get_partition_set(graphene_info, repository_selector, partition_set_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(repository_selector, 'repository_selector', RepositorySelector)
    check.str_param(partition_set_name, 'partition_set_name')
    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    partition_sets = repository.get_external_partition_sets()
    for partition_set in partition_sets:
        if partition_set.name == partition_set_name:
            return graphene_info.schema.type_named('PartitionSet')(
                external_repository_handle=repository.handle, external_partition_set=partition_set,
            )

    return graphene_info.schema.type_named('PartitionSetNotFoundError')(partition_set_name)


@capture_dauphin_error
def get_partition_by_name(graphene_info, repository_handle, partition_set, partition_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.inst_param(partition_set, 'partition_set', ExternalPartitionSet)
    check.str_param(partition_name, 'partition_name')
    return graphene_info.schema.type_named('Partition')(
        external_repository_handle=repository_handle,
        external_partition_set=partition_set,
        partition_name=partition_name,
    )


def get_partition_config(repository_handle, partition_set_name, partition_name):
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')

    return sync_get_external_partition(
        repository_handle, partition_set_name, partition_name
    ).run_config


def get_partition_tags(repository_handle, partition_set_name, partition_name):
    check.inst_param(repository_handle, 'repository_handle', RepositoryHandle)
    check.str_param(partition_set_name, 'partition_set_name')
    check.str_param(partition_name, 'partition_name')
    return sync_get_external_partition(repository_handle, partition_set_name, partition_name).tags
