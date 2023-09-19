from typing import Iterable

import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetsDefinition,
    AutoMaterializePolicy,
    DagsterInstance,
    Definitions,
    Output,
    _check as check,
    asset,
    job,
    op,
)
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.observable_asset import create_unexecutable_observable_assets_def


def test_observable_asset_basic_creation() -> None:
    assets_def = create_unexecutable_observable_assets_def(
        specs=[
            AssetSpec(
                key="observable_asset_one",
                # multi-asset does not support description lol
                # description="desc",
                metadata={"user_metadata": "value"},
                group_name="a_group",
            )
        ]
    )
    assert isinstance(assets_def, AssetsDefinition)

    expected_key = AssetKey(["observable_asset_one"])

    assert assets_def.key == expected_key
    # assert assets_def.descriptions_by_key[expected_key] == "desc"
    assert assets_def.metadata_by_key[expected_key]["user_metadata"] == "value"
    assert assets_def.group_names_by_key[expected_key] == "a_group"
    assert assets_def.is_asset_executable(expected_key) is False


def test_invalid_observable_asset_creation() -> None:
    invalid_specs = [
        AssetSpec("invalid_asset1", auto_materialize_policy=AutoMaterializePolicy.eager()),
        AssetSpec("invalid_asset2", code_version="ksjdfljs"),
        AssetSpec("invalid_asset2", freshness_policy=FreshnessPolicy(maximum_lag_minutes=1)),
        AssetSpec("invalid_asset2", skippable=True),
    ]

    for invalid_spec in invalid_specs:
        with pytest.raises(check.CheckError):
            create_unexecutable_observable_assets_def(specs=[invalid_spec])


def test_normal_asset_materializeable() -> None:
    @asset
    def an_asset() -> None: ...

    assert an_asset.is_asset_executable(AssetKey(["an_asset"])) is True


def test_observable_asset_creation_with_deps() -> None:
    asset_two = AssetSpec("observable_asset_two")
    assets_def = create_unexecutable_observable_assets_def(
        specs=[
            AssetSpec(
                "observable_asset_one",
                deps=[asset_two.key],  # todo remove key when asset deps accepts it
            )
        ]
    )
    assert isinstance(assets_def, AssetsDefinition)

    expected_key = AssetKey(["observable_asset_one"])

    assert assets_def.key == expected_key
    assert assets_def.asset_deps[expected_key] == {
        AssetKey(["observable_asset_two"]),
    }


def test_demonstrate_op_job_over_observable_assets() -> None:
    @op
    def an_op_that_emits() -> Iterable:
        yield AssetMaterialization(asset_key="asset_one")
        yield Output(None)

    @job
    def a_job_that_emits() -> None:
        an_op_that_emits()

    instance = DagsterInstance.ephemeral()

    asset_one = create_unexecutable_observable_assets_def([AssetSpec("asset_one")])

    defs = Definitions(assets=[asset_one], jobs=[a_job_that_emits])

    assert defs.get_job_def("a_job_that_emits").execute_in_process(instance=instance).success

    mat_event = instance.get_latest_materialization_event(asset_key=AssetKey("asset_one"))

    assert mat_event
    assert mat_event.asset_materialization
    assert mat_event.asset_materialization.asset_key == AssetKey("asset_one")
