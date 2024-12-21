from dagster._core.definitions.asset_key import AssetKey

from dagster_components_tests.integration_tests.component_loader import load_test_component_defs


def test_definitions_object_component_with_default_file() -> None:
    defs = load_test_component_defs("definitions/definitions_object")
    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}
