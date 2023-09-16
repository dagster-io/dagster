from dagster import AssetKey, AssetsDefinition, DagsterInstance, asset
from dagster._core.definitions.asset_spec import ObservableAssetSpec
from dagster._core.definitions.events import AssetMaterialization, AssetObservation
from dagster._core.definitions.observable_asset import (
    create_observable_assets_def,
    report_runless_asset_materialization,
    report_runless_asset_observation,
)
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType


def test_observable_asset_basic_creation() -> None:
    assets_def = create_observable_assets_def(
        specs=[
            ObservableAssetSpec(
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


def test_normal_asset_mateiralizeable() -> None:
    @asset
    def an_asset() -> None: ...

    assert an_asset.is_asset_executable(AssetKey(["an_asset"])) is True


def test_observable_asset_creation_with_deps() -> None:
    asset_two = ObservableAssetSpec("observable_asset_two")
    assets_def = create_observable_assets_def(
        specs=[
            ObservableAssetSpec(
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


def test_report_runless_materialization() -> None:
    instance = DagsterInstance.ephemeral()

    report_runless_asset_materialization(
        asset_materialization=AssetMaterialization(asset_key="observable_asset_one"),
        instance=instance,
    )

    mat_event = instance.get_latest_materialization_event(
        asset_key=AssetKey("observable_asset_one")
    )

    assert mat_event
    assert mat_event.asset_materialization
    assert mat_event.asset_materialization.asset_key == AssetKey("observable_asset_one")


def test_report_runless_observation() -> None:
    instance = DagsterInstance.ephemeral()

    report_runless_asset_observation(
        asset_observation=AssetObservation(asset_key="observable_asset_one"),
        instance=instance,
    )

    observations = instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_OBSERVATION,
            asset_key=AssetKey("observable_asset_one"),
        ),
        limit=1,
    )

    observation = next(iter(observations), None)
    assert observation

    assert observation.asset_key == AssetKey("observable_asset_one")
