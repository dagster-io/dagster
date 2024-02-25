from dagster import asset
from dagster._core.definitions.events import AssetKey
from dagster._core.reactive_scheduling.scheduling_policy import SchedulingPolicy


def test_include_scheduling_policy() -> None:
    assert SchedulingPolicy


def test_scheduling_policy_parameter():
    scheduling_policy = SchedulingPolicy()

    @asset(scheduling_policy=scheduling_policy)
    def an_asset():
        raise Exception("never executed")

    assert an_asset.scheduling_policies_by_key[AssetKey(["an_asset"])] is scheduling_policy
