from datetime import datetime
from typing import Optional, Sequence

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.instance import DagsterInstance

from .partition import Partition, PartitionsDefinition


@experimental
class RuntimePartitionsDefinition(PartitionsDefinition):
    """
    TODO docstring
    """

    def __init__(self, name: str):
        self._name = check.str_param(name, "name")
        self._instance = DagsterInstance.get()

    def get_partitions(self, current_time: Optional[datetime] = None) -> Sequence[Partition[str]]:
        keys = self._instance.get_runtime_partitions(self._name)
        return [Partition(key) for key in keys]

    def add_partitions(self, partition_keys: Sequence[str]) -> None:
        check.sequence_param(partition_keys, "partition_keys", of_type=str)
        self._instance.add_runtime_partitions(self._name, partition_keys)

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        return isinstance(other, RuntimePartitionsDefinition) and self._name == other._name

    def __hash__(self):
        return hash(self._name)

    def __str__(self) -> str:
        return f"Runtime-partitioned with name '{self._name}'"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self._name})"
