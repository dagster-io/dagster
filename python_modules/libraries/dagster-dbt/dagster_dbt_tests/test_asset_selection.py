import json

import pytest
from dagster._check import ParameterCheckError
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey
from dagster._utils import file_relative_path
from dagster_dbt import DbtManifestAssetSelection
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest


def get_previous_state_path():
    """Make sure we're providing a compatible previous manifest.json object."""
    import dbt.version
    from packaging import version

    if version.parse(dbt.version.__version__) >= version.parse("1.4.0"):
        return file_relative_path(__file__, "sample_previous_state_v8")
    else:
        return file_relative_path(__file__, "sample_previous_state_v7")


@pytest.mark.parametrize(
    "select,exclude,expected_asset_names",
    [
        (
            "*",
            None,
            {
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
            },
        ),
        (
            "+least_caloric",
            None,
            {"sort_by_calories", "subdir_schema/least_caloric"},
        ),
        (
            "sort_by_calories least_caloric",
            None,
            {"sort_by_calories", "subdir_schema/least_caloric"},
        ),
        (
            "tag:bar+",
            None,
            {
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
            },
        ),
        (
            "tag:foo",
            None,
            {"sort_by_calories", "cold_schema/sort_cold_cereals_by_calories"},
        ),
        (
            "tag:foo,tag:bar",
            None,
            {"sort_by_calories"},
        ),
        (
            None,
            "sort_hot_cereals_by_calories",
            {
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
            },
        ),
        (
            None,
            "+least_caloric",
            {"cold_schema/sort_cold_cereals_by_calories", "sort_hot_cereals_by_calories"},
        ),
        (
            None,
            "sort_by_calories least_caloric",
            {"cold_schema/sort_cold_cereals_by_calories", "sort_hot_cereals_by_calories"},
        ),
        (None, "tag:foo", {"subdir_schema/least_caloric", "sort_hot_cereals_by_calories"}),
    ],
)
def test_dbt_asset_selection(select, exclude, expected_asset_names):
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest_json = json.load(f)

    expected_keys = {AssetKey(key.split("/")) for key in expected_asset_names}

    dbt_assets = load_assets_from_dbt_manifest(manifest_json=manifest_json)
    asset_graph = AssetGraph.from_assets(dbt_assets)
    actual_keys = DbtManifestAssetSelection(
        manifest_json=manifest_json, select=select or "*", exclude=exclude or ""
    ).resolve_inner(asset_graph)

    assert expected_keys == actual_keys


def test_dbt_asset_selection_with_state():
    """Changes from previous state to sample_manifest.json.

    - sort_cold_cereals_by_calories has an updated definition
    - added subdir/least_caloric

    So we expect state:modified to select both of those assets.
    """
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest_json = json.load(f)

    dbt_assets = load_assets_from_dbt_manifest(manifest_json=manifest_json)
    asset_graph = AssetGraph.from_assets(dbt_assets)

    actual_keys = DbtManifestAssetSelection(
        manifest_json_path=manifest_path,
        select="state:modified",
        state_path=file_relative_path(__file__, get_previous_state_path()),
    ).resolve_inner(asset_graph)

    assert actual_keys == {
        AssetKey(["cold_schema", "sort_cold_cereals_by_calories"]),
        AssetKey(["subdir_schema", "least_caloric"]),
    }


def test_dbt_asset_selection_with_state_wrong_argument():
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r", encoding="utf8") as f:
        manifest_json = json.load(f)

    dbt_assets = load_assets_from_dbt_manifest(manifest_json=manifest_json)
    asset_graph = AssetGraph.from_assets(dbt_assets)

    with pytest.raises(ParameterCheckError, match="state selector"):
        DbtManifestAssetSelection(
            manifest_json=manifest_json,
            select="state:modified",
            state_path=file_relative_path(__file__, get_previous_state_path()),
        ).resolve_inner(asset_graph)
