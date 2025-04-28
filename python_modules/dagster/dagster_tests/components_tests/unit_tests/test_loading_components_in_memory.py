# # from dagster_test.components.simple_asset import SimpleAssetComponent


# # SimpleAssetComponent()
# from dagster.components.core.context import ComponentLoadContext, use_component_load_context
# from dagster.components.core.defs_module import get_component

from pathlib import Path

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.core.context import ComponentLoadContext, YamlComponentStorage
from dagster.components.core.defs_module import get_component


class InMemoryYamlComponentStorage(YamlComponentStorage):
    def __init__(self, yamls: dict) -> None:
        self.yamls = yamls

    def is_in_storage(self, context: "ComponentLoadContext") -> bool:
        return str(context.path) in self.yamls

    def read_declaration(self, context: "ComponentLoadContext") -> str:
        # This method should return the YAML declaration of the component.
        # For testing purposes, we can return a hardcoded YAML string.
        return self.yamls[str(context.path)]


def test_simple_asset_component_in_memory() -> None:
    yaml = """type: dagster_test.components.simple_asset.SimpleAssetComponent

attributes:
    asset_key: "simple_asset"
    value: "Hello, Dagster!"
    """

    path = (
        Path(__file__).parent
        / "component_loading_test_cases"
        / "test_simple_asset_component_in_memory"
        / "defs"
    )

    foo_path = str(path / "foo")
    context = ComponentLoadContext.for_test(
        path=path, yaml_component_storage=InMemoryYamlComponentStorage({foo_path: yaml})
    )

    root_component = get_component(context)

    assert root_component is not None
    defs = root_component.build_defs(context)
    assert isinstance(defs, Definitions)
    assert defs.get_assets_def("simple_asset")
