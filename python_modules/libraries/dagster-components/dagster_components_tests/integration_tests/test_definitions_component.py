import importlib
from pathlib import Path

from dagster._core.definitions.asset_key import AssetKey
from dagster_components.core.component import ComponentRegistry, get_registered_components_in_module
from dagster_components.core.component_defs_builder import (
    build_defs_from_component_path,
    get_component_name,
)
from dagster_components.core.deployment import CodeLocationProjectContext


def test_basic_load() -> None:
    package_name = "dagster_components.lib"
    dc_module = importlib.import_module(package_name)

    components = {}
    for component in get_registered_components_in_module(dc_module):
        key = f"dagster_components.{get_component_name(component)}"
        components[key] = component

    # import code

    # code.interact(local=locals())

    context = CodeLocationProjectContext(
        root_path=str(Path(__file__).parent),
        name="test",
        component_registry=ComponentRegistry(components),
        components_folder=(Path(__file__).parent / "components"),
    )

    defs = build_defs_from_component_path(
        path=Path(__file__).parent / "components" / "definitions_instance_one_default_file",
        registry=context.component_registry,
        resources={},
    )

    assert {spec.key for spec in defs.get_all_asset_specs()} == {AssetKey("an_asset")}
