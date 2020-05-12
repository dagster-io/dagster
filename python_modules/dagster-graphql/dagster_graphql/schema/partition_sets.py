import yaml
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_runs import get_runs
from dagster_graphql.schema.errors import (
    DauphinPartitionSetNotFoundError,
    DauphinPipelineNotFoundError,
    DauphinPythonError,
)

from dagster import check
from dagster.core.definitions.partition import Partition, PartitionSetDefinition
from dagster.core.storage.pipeline_run import PipelineRunsFilter


class DauphinPartition(dauphin.ObjectType):
    class Meta(object):
        name = 'Partition'

    name = dauphin.NonNull(dauphin.String)
    partition_set_name = dauphin.NonNull(dauphin.String)
    solid_subset = dauphin.List(dauphin.NonNull(dauphin.String))
    mode = dauphin.NonNull(dauphin.String)
    environmentConfigYaml = dauphin.NonNull(dauphin.String)
    tags = dauphin.non_null_list('PipelineTag')
    runs = dauphin.non_null_list('PipelineRun')

    def __init__(self, partition, partition_set):
        self._partition = check.inst_param(partition, 'partition', Partition)
        self._partition_set = check.inst_param(
            partition_set, 'partition_set', PartitionSetDefinition
        )

        super(DauphinPartition, self).__init__(
            name=partition.name,
            partition_set_name=partition_set.name,
            solid_subset=partition_set.solid_subset,
            mode=partition_set.mode,
        )

    def resolve_environmentConfigYaml(self, _):
        environment_dict = self._partition_set.environment_dict_for_partition(self._partition)
        return yaml.dump(environment_dict, default_flow_style=False)

    def resolve_tags(self, graphene_info):
        return [
            graphene_info.schema.type_named('PipelineTag')(key=key, value=value)
            for key, value in self._partition_set.tags_for_partition(self._partition).items()
        ]

    def resolve_runs(self, graphene_info):
        runs_filter = PipelineRunsFilter(
            tags={
                'dagster/partition_set': self._partition_set.name,
                'dagster/partition': self._partition.name,
            }
        )
        return get_runs(graphene_info, runs_filter)


class DauphinPartitions(dauphin.ObjectType):
    class Meta(object):
        name = 'Partitions'

    results = dauphin.non_null_list('Partition')


class DauphinPartitionSet(dauphin.ObjectType):
    class Meta(object):
        name = 'PartitionSet'

    name = dauphin.NonNull(dauphin.String)
    pipeline_name = dauphin.NonNull(dauphin.String)
    solid_subset = dauphin.List(dauphin.NonNull(dauphin.String))
    mode = dauphin.NonNull(dauphin.String)
    partitions = dauphin.Field(
        dauphin.NonNull('Partitions'),
        cursor=dauphin.String(),
        limit=dauphin.Int(),
        reverse=dauphin.Boolean(),
    )

    def __init__(self, partition_set):
        self._partition_set = check.inst_param(
            partition_set, 'partition_set', PartitionSetDefinition
        )

        super(DauphinPartitionSet, self).__init__(
            name=partition_set.name,
            pipeline_name=partition_set.pipeline_name,
            solid_subset=partition_set.solid_subset,
            mode=partition_set.mode,
        )

    def resolve_partitions(self, graphene_info, **kwargs):
        partitions = self._partition_set.get_partitions()

        cursor = kwargs.get("cursor")
        limit = kwargs.get("limit")
        reverse = kwargs.get('reverse')

        start = 0
        end = len(partitions)
        index = 0

        if cursor:
            index = next(
                (idx for (idx, partition) in enumerate(partitions) if partition.name == cursor),
                None,
            )

            if reverse:
                end = index
            else:
                start = index + 1

        if limit:
            if reverse:
                start = end - limit
            else:
                end = start + limit

        partitions = partitions[start:end]

        return graphene_info.schema.type_named('Partitions')(
            results=[
                graphene_info.schema.type_named('Partition')(
                    partition=partition, partition_set=self._partition_set
                )
                for partition in partitions
            ]
        )


class DapuphinPartitionSetOrError(dauphin.Union):
    class Meta(object):
        name = 'PartitionSetOrError'
        types = ('PartitionSet', DauphinPartitionSetNotFoundError, DauphinPythonError)


class DauphinPartitionSets(dauphin.ObjectType):
    class Meta(object):
        name = 'PartitionSets'

    results = dauphin.non_null_list('PartitionSet')


class DauphinPartitionSetsOrError(dauphin.Union):
    class Meta(object):
        name = 'PartitionSetsOrError'
        types = (DauphinPartitionSets, DauphinPipelineNotFoundError, DauphinPythonError)
