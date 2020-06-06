import yaml
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_runs import get_runs
from dagster_graphql.schema.errors import (
    DauphinPartitionSetNotFoundError,
    DauphinPipelineNotFoundError,
    DauphinPythonError,
)

from dagster import check
from dagster.core.definitions.partition import PartitionSetDefinition
from dagster.core.host_representation import ExternalPartitionSet
from dagster.core.storage.pipeline_run import PipelineRunsFilter


class DauphinPartition(dauphin.ObjectType):
    class Meta(object):
        name = 'Partition'

    name = dauphin.NonNull(dauphin.String)
    partition_set_name = dauphin.NonNull(dauphin.String)
    solid_selection = dauphin.List(dauphin.NonNull(dauphin.String))
    mode = dauphin.NonNull(dauphin.String)
    runConfigYaml = dauphin.NonNull(dauphin.String)
    tags = dauphin.non_null_list('PipelineTag')
    runs = dauphin.non_null_list('PipelineRun')

    def __init__(self, partition_name, partition_set_def, external_partition_set):
        self._partition_name = check.str_param(partition_name, 'partition_name')
        self._partition_set_def = check.inst_param(
            partition_set_def, 'partition_set_def', PartitionSetDefinition
        )
        self._external_partition_set = check.inst_param(
            external_partition_set, 'external_partition_set', ExternalPartitionSet
        )

        super(DauphinPartition, self).__init__(
            name=partition_name,
            partition_set_name=external_partition_set.name,
            solid_selection=external_partition_set.solid_selection,
            mode=external_partition_set.mode,
        )

    def resolve_runConfigYaml(self, _):
        partition = self._partition_set_def.get_partition(self._partition_name)
        environment_dict = self._partition_set_def.environment_dict_for_partition(partition)
        return yaml.dump(environment_dict, default_flow_style=False)

    def resolve_tags(self, graphene_info):
        partition = self._partition_set_def.get_partition(self._partition_name)
        tags = self._partition_set_def.tags_for_partition(partition).items()
        return [
            graphene_info.schema.type_named('PipelineTag')(key=key, value=value)
            for key, value in tags
        ]

    def resolve_runs(self, graphene_info):
        runs_filter = PipelineRunsFilter(
            tags={
                'dagster/partition_set': self._external_partition_set.name,
                'dagster/partition': self._partition_name,
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
    solid_selection = dauphin.List(dauphin.NonNull(dauphin.String))
    mode = dauphin.NonNull(dauphin.String)
    partitions = dauphin.Field(
        dauphin.NonNull('Partitions'),
        cursor=dauphin.String(),
        limit=dauphin.Int(),
        reverse=dauphin.Boolean(),
    )

    def __init__(self, partition_set_def, external_partition_set):
        self._partition_set_def = check.inst_param(
            partition_set_def, 'partition_set_def', PartitionSetDefinition
        )
        self._external_partition_set = check.inst_param(
            external_partition_set, 'external_partition_set', ExternalPartitionSet
        )

        super(DauphinPartitionSet, self).__init__(
            name=external_partition_set.name,
            pipeline_name=external_partition_set.pipeline_name,
            solid_selection=external_partition_set.solid_selection,
            mode=external_partition_set.mode,
        )

    def resolve_partitions(self, graphene_info, **kwargs):
        partition_names = self._external_partition_set.partition_names

        cursor = kwargs.get("cursor")
        limit = kwargs.get("limit")
        reverse = kwargs.get('reverse')

        start = 0
        end = len(partition_names)
        index = 0

        if cursor:
            index = next(
                (
                    idx
                    for (idx, partition_name) in enumerate(partition_names)
                    if partition_name == cursor
                ),
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

        partition_names = partition_names[start:end]

        return graphene_info.schema.type_named('Partitions')(
            results=[
                graphene_info.schema.type_named('Partition')(
                    partition_name=partition_name,
                    partition_set_def=self._partition_set_def,
                    external_partition_set=self._external_partition_set,
                )
                for partition_name in partition_names
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
