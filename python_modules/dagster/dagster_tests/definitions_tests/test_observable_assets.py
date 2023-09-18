from dagster import AssetKey, AssetsDefinition
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.observable_asset import create_unexecutable_observable_assets_def


def test_observable_asset_basic_creation() -> None:
    assets_def = create_unexecutable_observable_assets_def(
        asset_spec=AssetSpec(
            "observable_asset_one",
            description="desc",
            metadata={"user_metadata": "value"},
            group_name="a_group",
        )
    )
    assert isinstance(assets_def, AssetsDefinition)

    expected_key = AssetKey(["observable_asset_one"])

    assert assets_def.key == expected_key
    assert assets_def.descriptions_by_key[expected_key] == "desc"
    assert assets_def.metadata_by_key[expected_key] == {"user_metadata": "value"}
    assert assets_def.group_names_by_key[expected_key] == "a_group"


def test_observable_asset_creation_with_deps() -> None:
    asset_two = AssetSpec("observable_asset_two")
    assets_def = create_unexecutable_observable_assets_def(
        asset_spec=AssetSpec(
            "observable_asset_one",
            deps=[asset_two.key],  # todo remove key when asset deps accepts it
        )
    )
    assert isinstance(assets_def, AssetsDefinition)

    expected_key = AssetKey(["observable_asset_one"])

    assert assets_def.key == expected_key
    assert assets_def.asset_deps[expected_key] == {
        AssetKey(["observable_asset_two"]),
    }
