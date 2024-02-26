from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple, Optional, Set

from typing_extensions import TypeAlias

from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.sensor_enums import DefaultSensorStatus

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition.repository_definition import (
        RepositoryDefinition,
    )
    from dagster._core.instance import DagsterInstance

AssetPartition: TypeAlias = AssetKeyPartitionKey


class SchedulingResult(NamedTuple):
    launch: bool
    cursor: Optional[str] = None
    partition_keys: Optional[Set[str]] = None


class SchedulingExecutionContext(NamedTuple):
    # todo have this take the scheduling graph
    previous_tick_dt: Optional[datetime]
    tick_dt: datetime

    repository_def: "RepositoryDefinition"
    instance: "DagsterInstance"
    asset_key: AssetKey
    previous_cursor: Optional[str]


class RequestReaction(NamedTuple):
    include: bool


class TickSettings(NamedTuple):
    tick_cron: str
    sensor_name: Optional[str] = None
    description: Optional[str] = None
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED


class SchedulingPolicy:
    tick_settings: Optional[TickSettings] = None

    # TODO: support resources on schedule
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        ...

    def react_to_downstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        ...

    def react_to_upstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        ...


class DefaultSchedulingPolicy(SchedulingPolicy):
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=False)

    def react_to_downstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        return RequestReaction(include=False)
