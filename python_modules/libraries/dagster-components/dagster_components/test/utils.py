from pathlib import Path

from typing_extensions import TypeVar

from dagster_components import Component, ComponentLoadContext
from dagster_components.core.defs_module import DirectForTestComponentDecl

TComponent = TypeVar("TComponent", bound=Component)


def load_direct(
    component_type: type[TComponent],
    attribute_yaml: str,
) -> TComponent:
    decl_node = DirectForTestComponentDecl(
        path=Path("/"),
        component_type=component_type,
        attributes_yaml=attribute_yaml,
    )
    context = ComponentLoadContext.for_test(
        decl_node=decl_node,
    )
    components = decl_node.load(context)
    return components[0]  # type: ignore
