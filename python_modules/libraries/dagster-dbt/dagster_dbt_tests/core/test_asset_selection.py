import json
import os
from pathlib import Path
from typing import Optional, Set

import pytest
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey
from dagster_dbt import build_dbt_asset_selection
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.dbt_manifest import DbtManifestParam

manifest_path = Path(__file__).joinpath("..", "..", "sample_manifest.json").resolve()

with open(manifest_path, "r") as f:
    manifest = json.load(f)


@pytest.mark.parametrize(
    ["select", "exclude", "expected_asset_names"],
    [
        (
            "fqn:*",
            None,
            {
                "sort_by_calories",
                "cold_schema/sort_cold_cereals_by_calories",
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
                "cereals",
            },
        ),
        (
            "+least_caloric",
            None,
            {"sort_by_calories", "subdir_schema/least_caloric", "cereals"},
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
                "orders_snapshot",
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
                "cereals",
                "orders_snapshot",
            },
        ),
        (
            None,
            "+least_caloric",
            {
                "cold_schema/sort_cold_cereals_by_calories",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
            },
        ),
        (
            None,
            "sort_by_calories least_caloric",
            {
                "cold_schema/sort_cold_cereals_by_calories",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
                "cereals",
            },
        ),
        (
            None,
            "tag:foo",
            {
                "subdir_schema/least_caloric",
                "sort_hot_cereals_by_calories",
                "orders_snapshot",
                "cereals",
            },
        ),
    ],
)
def test_dbt_asset_selection(
    select: Optional[str], exclude: Optional[str], expected_asset_names: Set[str]
) -> None:
    expected_asset_keys = {AssetKey(key.split("/")) for key in expected_asset_names}

    @dbt_assets(manifest=manifest)
    def my_dbt_assets():
        ...

    asset_graph = AssetGraph.from_assets([my_dbt_assets])
    asset_selection = build_dbt_asset_selection(
        [my_dbt_assets],
        dbt_select=select or "fqn:*",
        dbt_exclude=exclude,
    )
    selected_asset_keys = asset_selection.resolve(all_assets=asset_graph)

    assert selected_asset_keys == expected_asset_keys


@pytest.mark.parametrize("manifest", [manifest, manifest_path, os.fspath(manifest_path)])
def test_dbt_asset_selection_manifest_argument(manifest: DbtManifestParam) -> None:
    expected_asset_keys = {
        AssetKey(key.split("/"))
        for key in {
            "sort_by_calories",
            "cold_schema/sort_cold_cereals_by_calories",
            "subdir_schema/least_caloric",
            "sort_hot_cereals_by_calories",
            "orders_snapshot",
            "cereals",
        }
    }

    @dbt_assets(manifest=manifest)
    def my_dbt_assets():
        ...

    asset_graph = AssetGraph.from_assets([my_dbt_assets])
    asset_selection = build_dbt_asset_selection([my_dbt_assets], dbt_select="fqn:*")
    selected_asset_keys = asset_selection.resolve(all_assets=asset_graph)

    assert selected_asset_keys == expected_asset_keys
