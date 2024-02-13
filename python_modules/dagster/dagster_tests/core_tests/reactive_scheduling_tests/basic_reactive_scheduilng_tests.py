from typing import Optional

from dagster import asset
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.reactive_scheduling.reactive_policy import SchedulingPolicy, SchedulingResult


def scheduling_policy_of_asset(
    assets_def: AssetsDefinition, asset_key: Optional[CoercibleToAssetKey] = None
) -> SchedulingPolicy:
    if asset_key:
        return assets_def.scheduling_policy_by_key[AssetKey.from_coercible(asset_key)]
    else:
        return assets_def.scheduling_policy_by_key[assets_def.key]


def test_thread_through_asset_property() -> None:
    class EmptySchedulingPolicy(SchedulingPolicy):
        ...

    @asset(
        scheduling_policy=EmptySchedulingPolicy(),
    )
    def an_asset() -> None:
        ...

    assert isinstance(scheduling_policy_of_asset(an_asset), EmptySchedulingPolicy)
    assert isinstance(scheduling_policy_of_asset(an_asset, "an_asset"), EmptySchedulingPolicy)


def test_creation_of_sensor() -> None:
    class SchedulingPolicyWithTick(SchedulingPolicy):
        tick_cron = "*/1 * * * *"

        def schedule(self) -> SchedulingResult:
            return SchedulingResult(execute=True)

    @asset(
        scheduling_policy=SchedulingPolicyWithTick(),
    )
    def an_asset() -> None:
        ...

    defs = Definitions([an_asset])
    assert len(defs.get_repository_def().sensor_defs) == 1
    sensor_def = defs.get_repository_def().sensor_defs[0]
    assert "reactive_scheduling_sensor" in sensor_def.name
