from typing import Tuple

from dagster import asset, multi_asset
from dagster._core.declarative_scheduling.policy import SchedulingPolicy
from dagster._core.definitions.asset_spec import AssetSpec


def test_basic_scheduling_policy_inclusion() -> None:
    scheduling_policy = SchedulingPolicy()

    @asset(metadata={SchedulingPolicy.METADATA_KEY: scheduling_policy})
    def an_asset() -> None: ...

    assert SchedulingPolicy.of_assets_def(an_asset, an_asset.key) is scheduling_policy
    assert SchedulingPolicy.of_assets_def(an_asset) is scheduling_policy

    scheduling_policy_one = SchedulingPolicy()
    scheduling_policy_two = SchedulingPolicy()

    specs = [
        # https://linear.app/dagster-labs/issue/FOU-99/more-principled-approach-to-unserializable-metadata for context
        # on the type ignores
        AssetSpec("asset_one", metadata={SchedulingPolicy.METADATA_KEY: scheduling_policy_one}),  # type: ignore
        AssetSpec("asset_two", metadata={SchedulingPolicy.METADATA_KEY: scheduling_policy_two}),  # type: ignore
    ]

    @multi_asset(specs=specs)
    def a_multi_asset() -> Tuple[None, None]: ...

    assert SchedulingPolicy.of_assets_def(a_multi_asset, "asset_one") is scheduling_policy_one
    assert SchedulingPolicy.of_assets_def(a_multi_asset, "asset_two") is scheduling_policy_two
