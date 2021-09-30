import json

from dagster import DependencyDefinition, ResourceDefinition
from dagster.core.asset_defs import build_assets_job
from dagster.utils import file_relative_path
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest


def test_load_from_manifest_json():
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r") as f:
        manifest_json = json.load(f)

    assets = load_assets_from_dbt_manifest(manifest_json=manifest_json)
    assert_assets_match_project(assets)


def assert_assets_match_project(assets):
    assert len(assets) == 4
    assets_by_name = {asset.name: asset for asset in assets}
    assert assets_by_name.keys() == {
        "sort_hot_cereals_by_calories",
        "sort_by_calories",
        "least_caloric",
        "sort_cold_cereals_by_calories",
    }
    for name, asset in assets_by_name.items():
        assert name == asset.name
        assert len(asset.output_defs) == 1
        assert f'["{name}"]' == asset.output_defs[0].hardcoded_asset_key.to_string()
        assert asset.tags == {"kind": "dbt"}

    job = build_assets_job(
        "jarb", assets, resource_defs={"dbt": ResourceDefinition.none_resource()}
    )
    assert job.dependencies == {
        "least_caloric": {
            "sort_by_calories": DependencyDefinition(
                solid="sort_by_calories",
                output="result",
            )
        },
        "sort_by_calories": {},
        "sort_cold_cereals_by_calories": {
            "sort_by_calories": DependencyDefinition(
                solid="sort_by_calories",
                output="result",
            )
        },
        "sort_hot_cereals_by_calories": {
            "sort_by_calories": DependencyDefinition(
                solid="sort_by_calories",
                output="result",
            )
        },
    }
