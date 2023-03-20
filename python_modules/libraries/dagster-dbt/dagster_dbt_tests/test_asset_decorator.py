from typing import AbstractSet, Optional

import pytest
from dagster import AssetKey, file_relative_path
from dagster._core.definitions.materialize import materialize
from dagster_dbt.asset_decorators import DbtExecutionContext, dbt_assets
from dagster_dbt.dbt_asset_resource import DbtAssetResource

from .utils import assert_assets_match_project


@pytest.mark.parametrize("prefix", [None, "foo", ["foo", "bar"]])
def test_structure(prefix) -> None:
    @dbt_assets(
        manifest_path=file_relative_path(__file__, "sample_manifest.json"),
        key_prefix=prefix,
    )
    def my_dbt_assets():
        ...

    assert_assets_match_project([my_dbt_assets], prefix=prefix)


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
def test_selections(
    dbt_build,
    conn_string,
    test_project_dir: str,
    test_profiles_dir: str,
    select: Optional[str],
    exclude: Optional[str],
    expected_asset_names: AbstractSet[str],
) -> None:
    @dbt_assets(
        manifest_path=file_relative_path(__file__, "sample_manifest.json"),
        select=select or "*",
        exclude=exclude or "",
    )
    def my_dbt_assets(context: DbtExecutionContext, dbt: DbtAssetResource):
        yield from dbt.cli(context, "run")

    expected_asset_keys = {AssetKey(key.split("/")) for key in expected_asset_names}
    assert my_dbt_assets.keys == expected_asset_keys

    result = materialize(
        [my_dbt_assets],
        resources={
            "dbt": DbtAssetResource(
                project_dir=test_project_dir,
                profiles_dir=test_profiles_dir,
            )
        },
    )

    assert result.success
    all_keys = {
        event.event_specific_data.materialization.asset_key  # type: ignore
        for event in result.all_events
        if event.event_type_value == "ASSET_MATERIALIZATION"
    }
    assert all_keys == expected_asset_keys
