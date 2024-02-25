from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional, Set

from typing_extensions import TypeAlias

from dagster._core.definitions.events import AssetKeyPartitionKey

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition.repository_definition import (
        RepositoryDefinition,
    )
    from dagster._core.instance import DagsterInstance

AssetPartition: TypeAlias = AssetKeyPartitionKey


class SchedulingResult(NamedTuple):
    launch: bool
    partition_keys: Optional[Set[str]] = None


class SchedulingExecutionContext(NamedTuple):
    evaluation_time: datetime
    repository_def: "RepositoryDefinition"
    instance: "DagsterInstance"


class RequestReaction(NamedTuple):
    include: bool
    pass


class SchedulingPolicy:
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        ...

    def request_from_downstream(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        ...

    def request_from_upstream(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        ...


class DefaultSchedulingPolicy(SchedulingPolicy):
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=False)

    def request_from_downstream(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        return RequestReaction(include=False)
