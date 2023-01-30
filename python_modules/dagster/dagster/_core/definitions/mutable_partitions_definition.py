from datetime import datetime
from typing import Optional, Sequence

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.instance import DagsterInstance

from .partition import (
    Partition,
    PartitionsDefinition,
    raise_error_on_invalid_partition_key_substring,
)


@experimental
class MutablePartitionsDefinition(PartitionsDefinition):
    """
    A partitions definition whose partition keys can be dynamically added and removed.

    This is useful for cases where the set of partitions is not known at definition time,
    but is instead determined at runtime.

    Partitions can be added and removed using the `add_partitions` and `remove_partitions` methods.
    For example:

    ```
    foo = MutablePartitionsDefinition("foo")

    @sensor(job=my_job)
    def my_sensor(context):
        foo.add_partitions([partition_key], instance=context.instance)
        return my_job.run_request_for_partition(partition_key, instance=context.instance)
    ```
    """

    def __init__(self, name: str):
        self._name = check.str_param(name, "name")

    def __str__(self) -> str:
        return f"Mutable partitions definition {self._name}"

    def get_partitions(
        self, current_time: Optional[datetime] = None, instance: Optional[DagsterInstance] = None
    ) -> Sequence[Partition[str]]:
        check.opt_inst_param(instance, "instance", DagsterInstance)

        if instance is None:
            check.failed("Must provide a dagster instance to fetch mutable partitions")

        keys = instance.get_mutable_partitions(self._name)
        return [Partition(key) for key in keys]

    def add_partitions(self, partition_keys: Sequence[str], instance: DagsterInstance) -> None:
        """
        Add partitions to the specified partition definition.
        Does not add any partitions that already exist.
        """
        check.sequence_param(partition_keys, "partition_keys", of_type=str)
        check.inst_param(instance, "instance", DagsterInstance)

        raise_error_on_invalid_partition_key_substring(partition_keys)
        instance.add_mutable_partitions(self._name, partition_keys)

    def has_partition(self, partition_key: str, instance: DagsterInstance) -> bool:
        """
        Checks if a partition key exists for the partitions definition.
        """
        check.str_param(partition_key, "partition_key")
        check.inst_param(instance, "instance", DagsterInstance)
        return instance.has_mutable_partition(self._name, partition_key)

    def delete_partition(self, partition_key: str, instance: DagsterInstance) -> None:
        """
        Delete a partition for the specified partition definition.
        If the partition does not exist, exits silently.
        """
        check.str_param(partition_key, "partition_key")
        check.inst_param(instance, "instance", DagsterInstance)
        instance.delete_mutable_partition(self._name, partition_key)

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        return isinstance(other, MutablePartitionsDefinition) and self._name == other._name

    def __hash__(self):
        return hash(self._name)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self._name})"
