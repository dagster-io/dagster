from typing import Tuple

from dagster import asset
from dagster._core.declarative_scheduling.scheduling_policy import (
    SYSTEM_METADATA_KEY_SCHEDULING_POLICY,
    SchedulingPolicy,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions


def test_include_scheduling_policy_asset_decorator() -> None:
    scheduling_policy_1 = SchedulingPolicy()

    @asset(metadata={SYSTEM_METADATA_KEY_SCHEDULING_POLICY: scheduling_policy_1})
    def an_asset() -> None: ...

    defs = Definitions(assets=[an_asset])
    assert defs.get_asset_graph().get(an_asset.key).scheduling_policy is scheduling_policy_1


def test_include_scheduling_policy_multi_asset_decorator() -> None:
    scheduling_policy_1 = SchedulingPolicy()
    scheduling_policy_2 = SchedulingPolicy()

    asset_1_key = AssetKey(["asset_1"])
    asset_2_key = AssetKey(["asset_2"])

    @multi_asset(
        outs={
            "asset_1_out": AssetOut(
                key=asset_1_key,
                metadata={SYSTEM_METADATA_KEY_SCHEDULING_POLICY: scheduling_policy_1},
            ),
            "asset_2_out": AssetOut(
                key=asset_2_key,
                metadata={SYSTEM_METADATA_KEY_SCHEDULING_POLICY: scheduling_policy_2},
            ),
        }
    )
    def _assets() -> Tuple: ...

    defs = Definitions(assets=[_assets])
    assert defs.get_asset_graph().get(asset_1_key).scheduling_policy is scheduling_policy_1
    assert defs.get_asset_graph().get(asset_2_key).scheduling_policy is scheduling_policy_2
