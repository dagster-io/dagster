import json

import pytest
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey
from dagster._utils import file_relative_path
from dagster_dbt import DbtManifestAssetSelection
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest


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
