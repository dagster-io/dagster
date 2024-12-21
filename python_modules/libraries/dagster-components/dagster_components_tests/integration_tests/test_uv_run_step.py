from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster._core.events import StepMaterializationData
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs


def get_materialization(
    result: ExecuteInProcessResult, key: CoercibleToAssetKey
) -> AssetMaterialization:
    asset_key = AssetKey.from_coercible(key)
    for event in result.get_asset_materialization_events():
        assert isinstance(event.event_specific_data, StepMaterializationData)
        if event.event_specific_data.materialization.asset_key == asset_key:
            return event.event_specific_data.materialization

    raise Exception(f"Materialization for asset key {asset_key} not found in result")


def remove_first_line(multi_string):
    lines = multi_string.split("\n")
    lines_without_first = lines[1:]
    return "\n".join(lines_without_first)


def test_definitions_component_with_default_file() -> None:
    defs = load_test_component_defs("native_steps/uv_run_hello_world")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}

    result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success
    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) == 1
    materialization = get_materialization(result, "an_asset")

    assert isinstance(materialization.metadata["foo"], TextMetadataValue)
    assert materialization.metadata["foo"].value == "bar"

    assert isinstance(materialization.metadata["cowsay"], TextMetadataValue)
    assert "hello world" in (materialization.metadata["cowsay"].value or "")
