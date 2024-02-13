from dataclasses import dataclass
from typing import Optional

from typing_extensions import TypeAlias

from dagster import _check as check
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.result import ObserveResult

# alias
AssetPartition: TypeAlias = AssetKeyPartitionKey


@dataclass(frozen=True)
class SchedulingResult:
    execute: bool
    override_versioning: bool = False


@dataclass(frozen=True)
class RequestReaction:
    execute: bool


class SchedulingPolicy:
    def __init__(self, sensor_name: Optional[str] = None):
        self.sensor_name = check.opt_str_param(sensor_name, "sensor_name")

    tick_cron = None

    # what about resources?
    def schedule(self) -> SchedulingResult:
        ...

    def observe(self) -> ObserveResult:
        ...

    # default to do nothing
    def react_to_downstream_request(self, asset_partition: AssetPartition) -> RequestReaction:
        return RequestReaction(execute=False)

    # default to do nothing
    def react_to_upstream_request(self, asset_partition: AssetPartition) -> RequestReaction:
        return RequestReaction(execute=False)
