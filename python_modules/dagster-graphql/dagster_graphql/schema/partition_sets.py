from dagster_graphql import dauphin
from dagster_graphql.schema.errors import (
    DauphinPartitionSetNotFoundError,
    DauphinPipelineNotFoundError,
    DauphinPythonError,
)

from dagster import check
from dagster.core.definitions.partition import PartitionSetDefinition


class DauphinPartition(dauphin.ObjectType):
    class Meta(object):
        name = 'Partition'

    name = dauphin.NonNull(dauphin.String)


class DauphinPartitionSet(dauphin.ObjectType):
    class Meta(object):
        name = 'PartitionSet'

    name = dauphin.NonNull(dauphin.String)
    pipeline_name = dauphin.NonNull(dauphin.String)
    partitions = dauphin.non_null_list('Partition')

    def __init__(self, partition_set):
        self._partition_set = check.inst_param(
            partition_set, 'partition_set', PartitionSetDefinition
        )

        super(DauphinPartitionSet, self).__init__(
            name=partition_set.name, pipeline_name=partition_set.pipeline_name
        )

    def resolve_partitions(self, _):
        partitions = self._partition_set.get_partitions()
        return partitions


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
