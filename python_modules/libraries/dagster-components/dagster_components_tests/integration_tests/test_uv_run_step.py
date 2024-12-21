from pathlib import Path

from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster._core.events import StepMaterializationData
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._utils import pushd

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


def text_metadata(materialization: AssetMaterialization, key: str) -> str:
    assert key in materialization.metadata
    metadata_value = materialization.metadata[key]
    assert isinstance(metadata_value, TextMetadataValue)
    assert metadata_value.value is not None
    return metadata_value.value


def test_uv_run_hello_world() -> None:
    defs = load_test_component_defs("native_steps/uv_run_hello_world")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}

    asset_spec = {spec.key: spec for spec in defs.get_all_asset_specs()}[AssetKey("an_asset")]
    assert asset_spec.description == "A description"

    assets_def = defs.get_asset_graph().assets_def_for_key(AssetKey("an_asset"))
    assert assets_def.op.name == "the_step"
    assert assets_def.op.tags == {"tag1": "value1", "tag2": "value2"}

    with pushd(str(Path(__file__).parent)):
        result = defs.get_implicit_global_asset_job_def().execute_in_process()
    assert result.success
    mat_events = result.get_asset_materialization_events()
    assert len(mat_events) == 1
    materialization = get_materialization(result, "an_asset")
    assert text_metadata(materialization, "foo") == "bar"
    cowsay_text = text_metadata(materialization, "cowsay")
    assert "hello world" in cowsay_text
    assert r"(oo)\_______" in cowsay_text
