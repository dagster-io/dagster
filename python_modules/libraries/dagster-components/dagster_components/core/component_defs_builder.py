from pathlib import Path
from typing import TYPE_CHECKING, List, Mapping, Optional, Sequence

from dagster._utils.warnings import suppress_dagster_warnings

from dagster_components.core.component import (
    Component,
    ComponentDeclNode,
    ComponentLoadContext,
    ComponentRegistry,
)
from dagster_components.core.component_decl_builder import (
    ComponentFolder,
    YamlComponentDecl,
    path_to_decl_node,
)
from dagster_components.core.deployment import CodeLocationProjectContext

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


def build_components_from_decl_node(
    context: ComponentLoadContext, decl_node: ComponentDeclNode
) -> Sequence[Component]:
    if isinstance(decl_node, YamlComponentDecl):
        parsed_defs = decl_node.defs_file_model
        component_type = context.registry.get(parsed_defs.component_type)
        return [component_type.from_decl_node(context, decl_node)]
    elif isinstance(decl_node, ComponentFolder):
        components = []
        for sub_decl in decl_node.sub_decls:
            components.extend(build_components_from_decl_node(context, sub_decl))
        return components

    raise NotImplementedError(f"Unknown component type {decl_node}")


def build_components_from_component_folder(
    context: ComponentLoadContext,
    path: Path,
) -> Sequence[Component]:
    component_folder = path_to_decl_node(path)
    assert isinstance(component_folder, ComponentFolder)
    return build_components_from_decl_node(context, component_folder)


def build_defs_from_component_path(
    path: Path,
    registry: ComponentRegistry,
    resources: Mapping[str, object],
) -> "Definitions":
    """Build a definitions object from a folder within the components hierarchy."""
    context = ComponentLoadContext(resources=resources, registry=registry)

    decl_node = path_to_decl_node(path=path)
    if not decl_node:
        raise Exception(f"No component found at path {path}")
    components = build_components_from_decl_node(context, decl_node)
    return defs_from_components(resources=resources, context=context, components=components)


@suppress_dagster_warnings
def defs_from_components(
    *,
    context: ComponentLoadContext,
    components: Sequence[Component],
    resources: Mapping[str, object],
) -> "Definitions":
    from dagster._core.definitions.definitions_class import Definitions

    return Definitions.merge(
        *[*[c.build_defs(context) for c in components], Definitions(resources=resources)]
    )


# Public method so optional Nones are fine
@suppress_dagster_warnings
def build_defs_from_toplevel_components_folder(
    path: Path,
    resources: Optional[Mapping[str, object]] = None,
    registry: Optional["ComponentRegistry"] = None,
) -> "Definitions":
    """Build a Definitions object from an entire component hierarchy."""
    from dagster._core.definitions.definitions_class import Definitions

    context = CodeLocationProjectContext.from_path(path, registry or ComponentRegistry.empty())

    all_defs: List[Definitions] = []
    for component in context.component_instances:
        component_path = Path(context.get_component_instance_path(component))
        defs = build_defs_from_component_path(
            path=component_path,
            registry=context.component_registry,
            resources=resources or {},
        )
        all_defs.append(defs)
    return Definitions.merge(*all_defs)
