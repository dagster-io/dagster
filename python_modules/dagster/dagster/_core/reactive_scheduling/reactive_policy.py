from dataclasses import dataclass
from typing import Optional

from typing_extensions import TypeAlias

from dagster import _check as check
from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.result import ObserveResult

# alias
AssetPartition: TypeAlias = AssetKeyPartitionKey


@dataclass(frozen=True)
class SchedulingResult:
    execute: bool
    tags: Optional[dict] = None


@dataclass(frozen=True)
class RequestReaction:
    execute: bool


# TODO: write variant that operates against subset directly for perf
# TODO: add base policy where you can tuck away asset conditions
class SchedulingPolicy:
    def __init__(self, sensor_name: Optional[str] = None):
        self.sensor_name = check.opt_str_param(sensor_name, "sensor_name")

    tick_cron = None

    # TODO support resources
    def schedule(self) -> SchedulingResult:
        ...

    # TODO support resources
    def observe(self) -> ObserveResult:
        ...

    # default to do nothing
    # note that I don't think ValidAssetSubset should be user facing API
    def react_to_downstream_request(self, downstream_subset: ValidAssetSubset) -> RequestReaction:
        return RequestReaction(execute=False)

    # default to do nothing
    # note that I don't think ValidAssetSubset should be user facing API
    def react_to_upstream_request(self, upstrean_subset: ValidAssetSubset) -> RequestReaction:
        return RequestReaction(execute=False)
