import importlib
import importlib.util
import inspect
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, List, Mapping, Optional, Sequence, Type

from dagster._utils.warnings import suppress_dagster_warnings

from dagster_components.core.component import (
    Component,
    ComponentLoadContext,
    ComponentTypeRegistry,
    TemplatedValueResolver,
    get_component_type_name,
    is_registered_component_type,
)
from dagster_components.core.component_decl_builder import (
    ComponentFolder,
    YamlComponentDecl,
    path_to_decl_node,
)
from dagster_components.core.deployment import CodeLocationProjectContext

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


def load_module_from_path(module_name, path) -> ModuleType:
    # Create a spec from the file path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None:
        raise ImportError(f"Cannot create a module spec from path: {path}")

    # Create and load the module
    module = importlib.util.module_from_spec(spec)
    assert spec.loader, "Must have a loader"
    spec.loader.exec_module(module)
    return module


def load_components_from_context(context: ComponentLoadContext) -> Sequence[Component]:
    if isinstance(context.decl_node, YamlComponentDecl):
        component_type = component_type_from_yaml_decl(context.registry, context.decl_node)
        context = context.with_rendering_scope(component_type.get_rendering_scope())
        return [component_type.load(context)]
    elif isinstance(context.decl_node, ComponentFolder):
        components = []
        for sub_decl in context.decl_node.sub_decls:
            components.extend(load_components_from_context(context.for_decl_node(sub_decl)))
        return components

    raise NotImplementedError(f"Unknown component type {context.decl_node}")


def component_type_from_yaml_decl(
    registry: ComponentTypeRegistry, decl_node: YamlComponentDecl
) -> Type[Component]:
    parsed_defs = decl_node.component_file_model
    if parsed_defs.type.startswith("."):
        component_registry_key = parsed_defs.type[1:]

        # Iterate over Python files in the folder
        for py_file in decl_node.path.glob("*.py"):
            module_name = py_file.stem

            # module = load_python_file(
            #     python_file=str(decl_node.path / f"{module_name}.py"),
            #     working_directory=str(decl_node.path.parent),
            # )
            py_path = str(decl_node.path / f"{module_name}.py")
            module = load_module_from_path(module_name, py_path)

            # print("**************")
            # print(f"Using {module_name} at {py_path} found module: {module} ")
            # print("**************")

            for _name, obj in inspect.getmembers(module, inspect.isclass):
                assert isinstance(obj, Type)
                if (
                    is_registered_component_type(obj)
                    and get_component_type_name(obj) == component_registry_key
                ):
                    return obj

        raise Exception(
            f"Could not find component type {component_registry_key} in {decl_node.path}"
        )

    return registry.get(parsed_defs.type)


def build_components_from_component_folder(
    context: ComponentLoadContext, path: Path
) -> Sequence[Component]:
    component_folder = path_to_decl_node(path)
    assert isinstance(component_folder, ComponentFolder)
    return load_components_from_context(context.for_decl_node(component_folder))


def loading_context_for_component_path(
    path: Path,
    registry: ComponentTypeRegistry,
    resources: Mapping[str, object],
) -> ComponentLoadContext:
    decl_node = path_to_decl_node(path=path)
    if not decl_node:
        raise Exception(f"No component found at path {path}")

    return ComponentLoadContext(
        resources=resources,
        registry=registry,
        decl_node=decl_node,
        templated_value_resolver=TemplatedValueResolver.default(),
    )


def build_components_from_component_path(
    path: Path,
    registry: ComponentTypeRegistry,
    resources: Mapping[str, object],
) -> Sequence[Component]:
    context = loading_context_for_component_path(path, registry, resources)
    return load_components_from_context(context)


def build_defs_from_component_path(
    path: Path,
    registry: ComponentTypeRegistry,
    resources: Mapping[str, object],
) -> "Definitions":
    """Build a definitions object from a folder within the components hierarchy."""
    decl_node = path_to_decl_node(path=path)
    if not decl_node:
        raise Exception(f"No component found at path {path}")

    context = ComponentLoadContext(
        resources=resources,
        registry=registry,
        decl_node=decl_node,
        templated_value_resolver=TemplatedValueResolver.default(),
    )
    components = load_components_from_context(context)
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
def build_component_defs(
    code_location_root: Path,
    resources: Optional[Mapping[str, object]] = None,
    registry: Optional["ComponentTypeRegistry"] = None,
    components_folder: Optional[Path] = None,
) -> "Definitions":
    """Build a Definitions object for all the component instances in a given code location.

    Args:
        code_location_root (Path): The path to the code location root.
            The path must be a code location directory that has a pyproject.toml with a [dagster] section.
    """
    from dagster._core.definitions.definitions_class import Definitions

    context = CodeLocationProjectContext.from_code_location_path(
        code_location_root,
        registry or ComponentTypeRegistry.from_entry_point_discovery(),
        components_folder=components_folder,
    )

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
