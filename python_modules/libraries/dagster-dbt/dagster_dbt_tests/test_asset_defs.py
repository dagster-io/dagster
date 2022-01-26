import json
from unittest.mock import MagicMock

from dagster import AssetKey, EventMetadataEntry, ResourceDefinition
from dagster.core.asset_defs import build_assets_job
from dagster.utils import file_relative_path
from dagster_dbt.asset_defs import load_assets_from_dbt_manifest
from dagster_dbt.types import DbtOutput


def test_load_from_manifest_json():
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r") as f:
        manifest_json = json.load(f)

    run_results_path = file_relative_path(__file__, "sample_run_results.json")
    with open(run_results_path, "r") as f:
        run_results_json = json.load(f)

    dbt_assets = load_assets_from_dbt_manifest(manifest_json=manifest_json)
    assert_assets_match_project(dbt_assets)

    dbt = MagicMock()
    dbt.run.return_value = DbtOutput(run_results_json)
    assets_job = build_assets_job(
        "assets_job",
        dbt_assets,
        resource_defs={"dbt": ResourceDefinition.hardcoded_resource(dbt)},
    )
    assert assets_job.execute_in_process().success


def test_runtime_metadata_fn():
    manifest_path = file_relative_path(__file__, "sample_manifest.json")
    with open(manifest_path, "r") as f:
        manifest_json = json.load(f)

    run_results_path = file_relative_path(__file__, "sample_run_results.json")
    with open(run_results_path, "r") as f:
        run_results_json = json.load(f)

    def runtime_metadata_fn(context, node_info):
        return {"op_name": context.solid_def.name, "dbt_model": node_info["name"]}

    dbt_assets = load_assets_from_dbt_manifest(
        manifest_json=manifest_json, runtime_metadata_fn=runtime_metadata_fn
    )
    assert_assets_match_project(dbt_assets)

    dbt = MagicMock()
    dbt.run.return_value = DbtOutput(run_results_json)
    assets_job = build_assets_job(
        "assets_job",
        dbt_assets,
        resource_defs={"dbt": ResourceDefinition.hardcoded_resource(dbt)},
    )
    result = assets_job.execute_in_process()
    assert result.success

    materializations = [
        event.event_specific_data.materialization
        for event in result.events_for_node(dbt_assets[0].op.name)
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 4
    assert materializations[0].metadata_entries == [
        EventMetadataEntry.text(dbt_assets[0].op.name, label="op_name"),
        EventMetadataEntry.text(materializations[0].asset_key.path[0], label="dbt_model"),
    ]


def assert_assets_match_project(dbt_assets):
    assert len(dbt_assets) == 1
    assets_op = dbt_assets[0].op
    assert assets_op.tags == {"kind": "dbt"}
    assert len(assets_op.input_defs) == 0
    assert assets_op.output_dict.keys() == {
        "sort_by_calories",
        "least_caloric",
        "sort_hot_cereals_by_calories",
        "sort_cold_cereals_by_calories",
    }
    for model_name in [
        "least_caloric",
        "sort_hot_cereals_by_calories",
        "sort_cold_cereals_by_calories",
    ]:
        out_def = assets_op.output_dict.get(model_name)
        assert out_def.hardcoded_asset_key == AssetKey([model_name])
        assert out_def.out_deps == ["sort_by_calories"]
        assert out_def.in_deps == []

    root_out_def = assets_op.output_dict.get("sort_by_calories")
    assert root_out_def.hardcoded_asset_key == AssetKey(["sort_by_calories"])
    assert root_out_def.out_deps == []
    assert out_def.in_deps == []
