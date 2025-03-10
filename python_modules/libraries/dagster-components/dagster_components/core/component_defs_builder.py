import importlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Optional

from dagster import Definitions
from dagster._annotations import deprecated
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    DefinitionsModuleCache,
    discover_entry_point_component_types,
)
from dagster_components.core.component_decl_builder import (
    ComponentDeclNode,
    ComponentFolder,
    YamlComponentDecl,
    path_to_decl_node,
)
from dagster_components.core.component_key import ComponentKey
from dagster_components.utils import get_path_from_module

if TYPE_CHECKING:
    from dagster import Definitions


def resolve_decl_node_to_yaml_decls(decl: ComponentDeclNode) -> list[YamlComponentDecl]:
    if isinstance(decl, YamlComponentDecl):
        return [decl]
    elif isinstance(decl, ComponentFolder):
        leaf_decls = []
        for sub_decl in decl.sub_decls:
            leaf_decls.extend(resolve_decl_node_to_yaml_decls(sub_decl))
        return leaf_decls

    raise NotImplementedError(f"Unknown component type {decl}")


def build_components_from_component_folder(
    context: ComponentLoadContext, path: Path
) -> Sequence[Component]:
    component_folder = path_to_decl_node(path)
    assert isinstance(component_folder, ComponentFolder)
    return component_folder.load(context.for_decl_node(component_folder))


@suppress_dagster_warnings
def defs_from_components(
    *,
    context: ComponentLoadContext,
    components: Sequence[Component],
    resources: Mapping[str, object],
) -> "Definitions":
    from dagster._core.definitions.definitions_class import Definitions

    return Definitions.merge(
        *[
            *[
                c.build_defs(context.with_rendering_scope(c.get_additional_scope()))
                for c in components
            ],
            Definitions(resources=resources),
        ]
    )


@deprecated(breaking_version="0.2.0")
@suppress_dagster_warnings
def build_component_defs(
    components_root: Path,
    resources: Optional[Mapping[str, object]] = None,
    component_types: Optional[dict[ComponentKey, type[Component]]] = None,
) -> "Definitions":
    """Build a Definitions object for all the component instances in a given code location.

    Args:
        components_root (Path): The path to the components root. This is a directory containing
            subdirectories with component instances.
    """
    defs_root = importlib.import_module(
        f"{Path(components_root).parent.name}.{Path(components_root).name}"
    )

    return load_defs(defs_root=defs_root, resources=resources, component_types=component_types)


# Public method so optional Nones are fine
@suppress_dagster_warnings
def load_defs(
    defs_root: ModuleType,
    resources: Optional[Mapping[str, object]] = None,
    component_types: Optional[dict[ComponentKey, type[Component]]] = None,
) -> "Definitions":
    """Constructs a Definitions object, loading all Dagster defs in the given module.

    Args:
        defs_root (Path): The path to the defs root, typically `package.defs`.
        resources (Optional[Mapping[str, object]]): A mapping of resource keys to resources
            to apply to the definitions.
        component_types (Optional[dict[ComponentKey, type[Component]]]): A mapping of
            component keys to component types.
    """
    from dagster._core.definitions.definitions_class import Definitions

    component_types = component_types or discover_entry_point_component_types()
    components_root_dir = get_path_from_module(defs_root)

    all_defs: list[Definitions] = []
    module_cache = DefinitionsModuleCache(resources=resources or {})
    for component_path in [item for item in components_root_dir.iterdir() if item.is_dir()]:
        defs = module_cache.load_defs(
            module=importlib.import_module(f"{defs_root.__name__}.{component_path.name}"),
        )
        all_defs.append(defs)
    return Definitions.merge(*all_defs)
