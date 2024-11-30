from pathlib import Path
from typing import TYPE_CHECKING, List, Mapping, Optional, Sequence

from dagster._components.core.component import Component, ComponentLoadContext, ComponentRegistry
from dagster._components.core.component_decl_builder import (
    ComponentFolder,
    YamlComponentDecl,
    find_component_decl,
)
from dagster._components.core.deployment import CodeLocationProjectContext

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


def build_component_hierarchy(
    context: ComponentLoadContext, component_folder: ComponentFolder
) -> Sequence[Component]:
    to_return = []
    for decl_node in component_folder.sub_decls:
        if isinstance(decl_node, YamlComponentDecl):
            parsed_defs = decl_node.defs_file_model
            component_type = context.registry.get(parsed_defs.component_type)
            to_return.append(component_type.from_decl_node(context, decl_node))
        elif isinstance(decl_node, ComponentFolder):
            to_return.extend(build_component_hierarchy(context, decl_node))
        else:
            raise NotImplementedError(f"Unknown component type {decl_node}")
    return to_return


def build_components_from_component_folder(
    context: ComponentLoadContext,
    path: Path,
) -> Sequence[Component]:
    component_folder = find_component_decl(path)
    assert isinstance(component_folder, ComponentFolder)
    return build_component_hierarchy(context, component_folder)


def build_defs_from_component_folder(
    path: Path,
    registry: ComponentRegistry,
    resources: Mapping[str, object],
) -> "Definitions":
    """Build a definitions object from a folder within the components hierarchy."""
    component_folder = find_component_decl(path=path)
    assert isinstance(component_folder, ComponentFolder)
    context = ComponentLoadContext(resources=resources, registry=registry)
    components = build_components_from_component_folder(context=context, path=path)
    return defs_from_components(resources=resources, context=context, components=components)


def defs_from_components(
    *,
    context: ComponentLoadContext,
    components: Sequence[Component],
    resources: Mapping[str, object],
) -> "Definitions":
    from dagster._core.definitions.definitions_class import Definitions

    return Definitions.merge_internal(
        [*[c.build_defs(context) for c in components], Definitions(resources=resources)]
    )


# Public method so optional Nones are fine
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
        defs = build_defs_from_component_folder(
            path=component_path,
            registry=context.component_registry,
            resources=resources or {},
        )
        all_defs.append(defs)
    return Definitions.merge_internal(all_defs)
