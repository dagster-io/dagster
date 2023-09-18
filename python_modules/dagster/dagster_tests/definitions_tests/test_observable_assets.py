from typing import Iterator, Optional

import pytest
from dagster import (
    AssetKey,
    AssetsDefinition,
    AutoMaterializePolicy,
    DagsterInstance,
    Output,
    _check as check,
    asset,
    materialize,
)
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.events import AssetObservation
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.observable_asset import (
    create_unexecutable_observable_assets_def,
)

# report_runless_asset_materialization,
# report_runless_asset_observation,
# TODO
from dagster._core.event_api import EventLogRecord, EventRecordsFilter
from dagster._core.events import DagsterEventType


def get_latest_observation_for_asset_key(
    instance: DagsterInstance, asset_key: AssetKey
) -> Optional[EventLogRecord]:
    observations = instance.get_event_records(
        EventRecordsFilter(event_type=DagsterEventType.ASSET_OBSERVATION, asset_key=asset_key),
        limit=1,
    )

    observation = next(iter(observations), None)
    return observation


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


# def test_report_runless_materialization() -> None:
#     instance = DagsterInstance.ephemeral()

#     report_runless_asset_materialization(
#         asset_materialization=AssetMaterialization(asset_key="observable_asset_one"),
#         instance=instance,
#     )

#     mat_event = instance.get_latest_materialization_event(
#         asset_key=AssetKey("observable_asset_one")
#     )

#     assert mat_event
#     assert mat_event.asset_materialization
#     assert mat_event.asset_materialization.asset_key == AssetKey("observable_asset_one")


# def test_report_runless_observation() -> None:
#     instance = DagsterInstance.ephemeral()

#     report_runless_asset_observation(
#         asset_observation=AssetObservation(asset_key="observable_asset_one"),
#         instance=instance,
#     )

#     observation = get_latest_observation_for_asset_key(
#         instance, asset_key=AssetKey("observable_asset_one")
#     )
#     assert observation

#     assert observation.asset_key == AssetKey("observable_asset_one")


def test_emit_asset_observation_in_user_space() -> None:
    # This test to exists to demonstrate that you cannot emit an asset observation without
    # it automatically emitting a materialization because of the None output. We will have
    # to fix this because being able to supplant observable source assets

    @asset(key="asset_in_user_space")
    def active_observable_asset_in_user_space() -> Iterator:
        # not ideal but it works
        yield AssetObservation(asset_key="asset_in_user_space", metadata={"foo": "bar"})
        yield Output(None)

    instance = DagsterInstance.ephemeral()

    # to avoid breaking your brain, think of this as "execute" or "refresh", not "materialize"
    assert materialize(assets=[active_observable_asset_in_user_space], instance=instance).success

    observation = get_latest_observation_for_asset_key(
        instance, asset_key=AssetKey("asset_in_user_space")
    )
    assert observation
    assert observation.asset_key == AssetKey("asset_in_user_space")

    mat_event = instance.get_latest_materialization_event(asset_key=AssetKey("asset_in_user_space"))

    # we actually want this to be false once we make changes to make mainline assets
    # replace observable source assets
    assert mat_event
