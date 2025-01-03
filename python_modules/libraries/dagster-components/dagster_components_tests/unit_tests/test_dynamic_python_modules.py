from pathlib import Path

from dagster_components.core.component import ComponentLoadContext
from dagster_components.core.component_decl_builder import (
    ComponentFileModel,
    ComponentKey,
    YamlComponentDecl,
)
from dagster_components.lib.definitions_component import get_python_module_name


def test_get_python_module_name() -> None:
    assert (
        get_python_module_name(
            context=ComponentLoadContext.for_test(
                code_location_name="test",
                decl_node=YamlComponentDecl(
                    key=ComponentKey(parts=["a", "b"]),
                    path=Path("a/b"),
                    component_file_model=ComponentFileModel(
                        type="some_type",
                        params={},
                    ),
                ),
            ),
            subkey="defs",
        )
        == "__dagster_code_location__.test.__component_instance__.a.b.__some_type__.defs"
    )
