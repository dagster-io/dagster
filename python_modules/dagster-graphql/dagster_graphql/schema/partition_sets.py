import yaml
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_partition_sets import (
    get_partition_by_name,
    get_partition_config,
    get_partition_tags,
)
from dagster_graphql.implementation.fetch_runs import get_runs
from dagster_graphql.schema.errors import (
    DauphinPartitionSetNotFoundError,
    DauphinPipelineNotFoundError,
    DauphinPythonError,
)

from dagster import check
from dagster.core.host_representation import ExternalPartitionSet, RepositoryHandle
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

    def __init__(self, external_repository_handle, external_partition_set, partition_name):
        self._external_repository_handle = check.inst_param(
            external_repository_handle, 'external_respository_handle', RepositoryHandle
        )
        self._external_partition_set = check.inst_param(
            external_partition_set, 'external_partition_set', ExternalPartitionSet
        )
        self._partition_name = check.str_param(partition_name, 'partition_name')

        super(DauphinPartition, self).__init__(
            name=partition_name,
            partition_set_name=external_partition_set.name,
            solid_selection=external_partition_set.solid_selection,
            mode=external_partition_set.mode,
        )

    def resolve_runConfigYaml(self, _):
        run_config = get_partition_config(
            self._external_repository_handle,
            self._external_partition_set.name,
            self._partition_name,
        )

        if run_config is None:
            # TODO: surface user-facing error here
            # https://github.com/dagster-io/dagster/issues/2576
            return ''

        return yaml.dump(run_config, default_flow_style=False)

    def resolve_tags(self, graphene_info):
        tags = get_partition_tags(
            self._external_repository_handle,
            self._external_partition_set.name,
            self._partition_name,
        )

        if tags is None:
            # TODO: surface user-facing error here
            # https://github.com/dagster-io/dagster/issues/2576
            return []

        return [
            graphene_info.schema.type_named('PipelineTag')(key=key, value=value)
            for key, value in tags.items()
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
    partition = dauphin.Field('Partition', partition_name=dauphin.NonNull(dauphin.String))

    def __init__(self, external_repository_handle, external_partition_set):
        self._external_repository_handle = check.inst_param(
            external_repository_handle, 'external_respository_handle', RepositoryHandle
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
                    external_partition_set=self._external_partition_set,
                    external_repository_handle=self._external_repository_handle,
                    partition_name=partition_name,
                )
                for partition_name in partition_names
            ]
        )

    def resolve_partition(self, graphene_info, partition_name):
        return get_partition_by_name(
            graphene_info,
            self._external_repository_handle,
            self._external_partition_set,
            partition_name,
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
