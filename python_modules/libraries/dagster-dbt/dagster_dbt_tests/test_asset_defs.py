import json
from unittest.mock import MagicMock

from dagster import DependencyDefinition, EventMetadataEntry, ResourceDefinition
from dagster.core.asset_defs import build_assets_job
from dagster.utils import file_relative_path
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest


def test_load_from_manifest_json():
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r") as f:
        manifest_json = json.load(f)

    assets = load_assets_from_dbt_manifest(manifest_json=manifest_json)
    assert_assets_match_project(assets)

    dbt = MagicMock()
    assets_job = build_assets_job(
        "assets_job", assets, resource_defs={"dbt": ResourceDefinition.hardcoded_resource(dbt)}
    )
    assert assets_job.execute_in_process().success


def test_runtime_metadata_fn():
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r") as f:
        manifest_json = json.load(f)

    def runtime_metadata_fn(context, node_info):
        return {"op_name": context.solid_def.name, "dbt_model": node_info["name"]}

    assets = load_assets_from_dbt_manifest(
        manifest_json=manifest_json, runtime_metadata_fn=runtime_metadata_fn
    )
    assert_assets_match_project(assets)

    dbt = MagicMock()
    assets_job = build_assets_job(
        "assets_job", assets, resource_defs={"dbt": ResourceDefinition.hardcoded_resource(dbt)}
    )
    result = assets_job.execute_in_process()
    assert result.success

    for asset in assets:
        materializations = [
            event.event_specific_data.materialization
            for event in result.events_for_node(asset.op.name)
            if event.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(materializations) == 1
        assert materializations[0].metadata_entries == [
            EventMetadataEntry.text(asset.op.name, label="op_name"),
            EventMetadataEntry.text(asset.op.name, label="dbt_model"),
        ]


def assert_assets_match_project(assets):
    assert len(assets) == 4
    assets_by_name = {asset.op.name: asset for asset in assets}
    assert assets_by_name.keys() == {
        "sort_hot_cereals_by_calories",
        "sort_by_calories",
        "least_caloric",
        "sort_cold_cereals_by_calories",
    }
    for name, asset in assets_by_name.items():
        assert name == asset.op.name
        assert len(asset.op.output_defs) == 1
        assert f'["{name}"]' == asset.op.output_defs[0].hardcoded_asset_key.to_string()
        assert asset.op.tags == {"kind": "dbt"}

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
