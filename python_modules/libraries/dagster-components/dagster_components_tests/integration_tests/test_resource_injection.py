import pytest
from dagster import AssetKey, Definitions
from dagster._core.definitions.materialize import materialize

from dagster_components_tests.integration_tests.component_loader import chdir as chdir


@pytest.mark.parametrize("defs", ["resource_injection/nested_component"], indirect=True)
def test_nested_component(defs: Definitions) -> None:
    assert "some_resource" in (defs.resources or {})
    assert len(defs.get_all_asset_specs()) == 2

    assets_def = defs.get_asset_graph().assets_def_for_key(AssetKey("an_asset"))
    assert assets_def is not None

    result = materialize(assets=[assets_def])
    assert result.success
    # gets the value of the resource that was paassed at load time
    assert result.output_for_node("an_asset") == "some_value"

    assets_def = defs.get_asset_graph().assets_def_for_key(AssetKey("an_asset_calls_execute"))

    result = materialize(assets=[assets_def])
    assert result.success
    # gets the value of the resource that was paassed at load time
    assert result.output_for_node("an_asset_calls_execute") == "some_value"


@pytest.mark.parametrize("defs", ["resource_injection/peer_pythonic_component"], indirect=True)
def test_peer_component(defs: Definitions) -> None:
    assert "some_resource" in (defs.resources or {})
