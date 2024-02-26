from datetime import datetime
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.reactive_scheduling.reactive_scheduling_plan import (
    PulseResult,
    pulse_policy_on_asset,
)
from dagster._core.reactive_scheduling.scheduling_policy import (
    AssetPartition,
    RequestReaction,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
)
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


def run_scheduling_pulse_on_asset(
    defs: Definitions,
    asset_key: CoercibleToAssetKey,
    queryer: Optional[CachingInstanceQueryer] = None,
    evaluation_dt: Optional[datetime] = None,
    previous_dt: Optional[datetime] = None,
    previous_cursor: Optional[str] = None,
) -> PulseResult:
    return pulse_policy_on_asset(
        asset_key=AssetKey.from_coercible(asset_key),
        repository_def=defs.get_repository_def(),
        queryer=queryer or CachingInstanceQueryer.ephemeral(defs),
        tick_dt=evaluation_dt or datetime.now(),
        previous_tick_dt=previous_dt,
        previous_cursor=previous_cursor,
    )


class AlwaysLaunchSchedulingPolicy(SchedulingPolicy):
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=True)


class AlwaysDeferSchedulingPolicy(SchedulingPolicy):
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=False)

    def react_to_downstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        return RequestReaction(include=True)

    def react_to_upstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        return RequestReaction(include=True)
