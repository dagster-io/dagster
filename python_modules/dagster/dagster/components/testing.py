import importlib
import secrets
import shutil
import string
import sys

import yaml
from dagster_shared import check

"""Testing utilities for components."""

import json
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import alter_sys_path
from dagster.components.component.component import Component
from dagster.components.component_scaffolding import scaffold_object
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import (
    CompositeYamlComponent,
    get_component,
    load_yaml_component_from_path,
)
from dagster.components.scaffold.scaffold import ScaffoldFormatOptions


def component_defs(
    *,
    component: Component,
    resources: Optional[Mapping[str, Any]] = None,
    context: Optional[ComponentLoadContext] = None,
) -> Definitions:
    """Builds a Definitions object from a Component.


    Args:
        component (Component): The Component to build the Definitions from.
        resources (Optional[Mapping[str, Any]]): A dictionary of resources to pass to the Component.
        context (Optional[ComponentLoadContext]): A ComponentLoadContext to pass to the Component. Defaults to a test context.

    Examples:

        .. code-block:: python

            # SimpleComponent produces an asset "an_asset"
            an_asset = component_defs(component=SimpleComponent()).get_assets_def("an_asset")
            assert an_asset.key == AssetKey("an_asset")

        .. code-block:: python

            # RequiresResoureComponent produces an asset "an_asset" and requires a resource "my_resource"
            an_asset = component_defs(
                component=SimpleComponent(),
                resources={"my_resource": MyResource()},
            ).get_assets_def("an_asset")
            assert an_asset.key == AssetKey("an_asset")
    """
    context = context or ComponentLoadContext.for_test()
    return component.build_defs(context).with_resources(resources)


def defs_from_component_yaml_path(
    *,
    component_yaml: Path,
    context: Optional[ComponentLoadContext] = None,
    resources: Optional[dict[str, Any]] = None,
):
    context = context or ComponentLoadContext.for_test()
    component = load_yaml_component_from_path(context=context, component_def_path=component_yaml)
    return component_defs(component=component, resources=resources, context=context)


def get_original_module_name(cls):
    """Returns the fully qualified module name where a class was originally declared.

    Args:
        cls: A class object (not an instance)

    Returns:
        str: The fully qualified module name (e.g., 'foo.bar.SomeClass')

    Raises:
        TypeError: If the input is not a class
        AttributeError: If the class doesn't have proper module information
    """
    if not isinstance(cls, type):
        raise TypeError("Input must be a class, not an instance")

    # Get the module name where the class is defined
    module_name = cls.__module__

    # Get the class name
    class_name = cls.__qualname__  # Use __qualname__ to handle nested classes properly

    if not module_name:
        raise AttributeError(f"Class {cls} has no module name")

    # Combine them to get the fully qualified name
    return f"{module_name}.{class_name}"


def get_underlying_component(context: ComponentLoadContext) -> Optional[Component]:
    """Loads a component from the given context, resolving the underlying component if
    it is a CompositeYamlComponent.
    """
    component = get_component(context)
    if isinstance(component, CompositeYamlComponent):
        assert len(component.components) == 1
        return component.components[0]
    return component


def random_importable_name(length: int = 8) -> str:
    """Generate a random string that's guaranteed to be importable as a Python symbol."""
    # Ensure it starts with a letter (not underscore to avoid special meanings)
    first_char = secrets.choice(string.ascii_letters)

    # Use only letters and digits for the rest (no underscores for cleaner names)
    remaining_chars = string.ascii_letters + string.digits
    remaining = "".join(secrets.choice(remaining_chars) for _ in range(length - 1))

    return "sandbox_module_" + first_char + remaining


@dataclass
class DefsPathSandbox:
    project_root: Path
    defs_folder_path: Path
    component_path: Path
    project_name: str
    component_format: ScaffoldFormatOptions

    @contextmanager
    def swap_defs_file(self, defs_path: Path, component_body: Optional[dict[str, Any]]):
        check.invariant(
            defs_path.suffix == ".yaml",
            "Attributes are only supported for yaml components",
        )
        check.invariant(defs_path.exists(), "defs.yaml must exist")

        # no need to override there is no component body
        if component_body is None:
            yield
            return

        temp_dir = Path(tempfile.mkdtemp())
        temp_path = temp_dir / defs_path.name

        try:
            shutil.copy2(defs_path, temp_path)

            defs_path.write_text(yaml.safe_dump(component_body))

            yield

        finally:
            if temp_path.exists():
                defs_path.unlink(missing_ok=True)
                shutil.copy2(temp_path, defs_path)
            shutil.rmtree(temp_dir)

    @contextmanager
    def load(
        self, component_body: Optional[dict[str, Any]] = None
    ) -> Iterator[tuple["Component", "Definitions"]]:
        defs_path = self.defs_folder_path / "defs.yaml"

        with self.swap_defs_file(defs_path, component_body):
            with self.load_instance(0) as (component, defs):
                yield component, defs

    @contextmanager
    def load_instance(
        self, instance_key: Union[int, str]
    ) -> Iterator[tuple[Component, Definitions]]:
        assert isinstance(instance_key, int)  # only int for now
        with self.load_all() as components:
            yield components[instance_key][0], components[instance_key][1]

    @contextmanager
    def load_all(self) -> Iterator[list[tuple[Component, Definitions]]]:
        with alter_sys_path(to_add=[str(self.project_root / "src")], to_remove=[]):
            module_path = f"{self.project_name}.defs.{self.component_path}"
            try:
                yield get_all_components_defs_from_defs_path(
                    project_root=self.project_root,
                    component_path=self.component_path,
                    project_name=self.project_name,
                )

            finally:
                modules_to_remove = [name for name in sys.modules if name.startswith(module_path)]
                for name in modules_to_remove:
                    del sys.modules[name]


def flatten_components(parent_component: Optional[Component]) -> list[Component]:
    if isinstance(parent_component, CompositeYamlComponent):
        return list(parent_component.components)
    elif isinstance(parent_component, Component):
        return [parent_component]
    else:
        return []


def get_all_components_defs_from_defs_path(
    *,
    project_name: str,
    project_root: Path,
    component_path: Path,
    defs_module_name: str = "defs",
) -> list[tuple[Component, Definitions]]:
    module_path = f"{project_name}.{defs_module_name}.{component_path}"
    module = importlib.import_module(module_path)
    context = ComponentLoadContext.for_module(
        defs_module=module,
        project_root=project_root,
        terminate_autoloading_on_keyword_files=False,
    )
    components = flatten_components(get_component(context))
    return [(component, component.build_defs(context)) for component in components]


def get_component_defs_from_defs_path(
    *,
    project_name: str,
    project_root: Path,
    component_path: Path,
) -> tuple[Component, Definitions]:
    components = get_all_components_defs_from_defs_path(
        project_name=project_name, project_root=project_root, component_path=component_path
    )
    check.invariant(
        len(components) == 1,
        "Only one component is supported. To get all components use get_all_components_defs_from_defs_path.",
    )
    return components[0]


@contextmanager
def scaffold_defs_sandbox(
    *,
    component_cls: type,
    component_path: Optional[Union[Path, str]] = None,
    scaffold_params: Optional[dict[str, Any]] = None,
    scaffold_format: ScaffoldFormatOptions = "yaml",
    project_name: Optional[str] = None,
) -> Iterator[DefsPathSandbox]:
    """Create a lightweight sandbox to scaffold and instantiate a component. Useful
    for those authoring component types.

    Scaffold defs sandbox creates a temporary project that mimics the defs folder portion
    of a real dagster project.

    It then invokes the scaffolder on the component class that produces. After
    scaffold_defs_sandbox yields a DefsPathSandbox object.

    DefsPathSandbox has a few properties useful for different types of tests:

    * defs_folder_path: The absolute path to the defs folder where the component
      is scaffolded. The user can inspect and load files that the scaffolder has produced.
      e.g. (defs_folder_path / "defs.yaml").exists()

    * component_path: The relative path to the component within the defs folder. If not
      provided, a random name is generated.

    * project_name: If not provided, a random name is generated.

    Once the sandbox is created the user has the option to load the definitions produced
    by the component using the load method on DefsPathSandbox.

    By default it will produce the component based on the persisted `defs.yaml` file. You
    can also supply a component body to the load method to override the defs.yaml file with
    an in-memory component body.

    This sandbox does not provide complete environmental isolation, but does provide some isolation guarantees
    to do its best to isolate the test from and restore the environment after the test.

    * A file structure like this is created: <<temp folder>> / src / <<project_name>> / defs / <<component_path>>
    * <<temp folder>> / src is placed in sys.path during the loading process
    * The last element of the component path is loaded as a namespace package
    * Any modules loaded during the process that descend from defs module are evicted from sys.modules on cleanup.

    Args:
        component_cls: The component class to scaffold
        component_path: Optional path where the component should be scaffolded. It is relative to the defs folder. Defaults to a random name at the root of the defs folder.
        scaffold_params: Optional parameters to pass to the scaffolder in dictionary form. E.g. if you scaffold a component with dg scaffold defs MyComponent --param-one value-one the scaffold_params should be {"param_one": "value-one"}.
        scaffold_format: Format to use for scaffolding (default: "yaml"). Can also be "python".
        project_name: Optional name for the project (default: random name).

    Returns:
        Iterator[DefsPathSandbox]: A context manager that yields a DefsPathSandbox

    Example:

    .. code-block:: python

        with scaffold_defs_sandbox(component_cls=MyComponent) as sandbox:
            assert (sandbox.defs_folder_path / "defs.yaml").exists()
            assert (sandbox.defs_folder_path / "my_component_config_file.yaml").exists()  # produced by MyComponentScaffolder

        with scaffold_defs_sandbox(component_cls=MyComponent, scaffold_params={"asset_key": "my_asset"}) as sandbox:
            with sandbox.load() as (component, defs):
                assert isinstance(component, MyComponent)
                assert defs.get_asset_def("my_asset").key == AssetKey("my_asset")

        with scaffold_defs_sandbox(component_cls=MyComponent) as sandbox:
            with sandbox.load(component_body={"type": "MyComponent", "attributes": {"asset_key": "different_asset_key"}}) as (component, defs):
                assert isinstance(component, MyComponent)
                assert defs.get_asset_def("different_asset_key").key == AssetKey("different_asset_key")
    """
    project_name = project_name or random_importable_name()
    component_path = component_path or random_importable_name()
    typename = get_original_module_name(component_cls)
    with tempfile.TemporaryDirectory() as project_root_str:
        project_root = Path(project_root_str)
        defs_folder_path = project_root / "src" / project_name / "defs" / component_path
        defs_folder_path.mkdir(parents=True, exist_ok=True)
        scaffold_object(
            path=defs_folder_path,
            # obj=component_cls,
            typename=typename,
            json_params=json.dumps(scaffold_params) if scaffold_params else None,
            scaffold_format=scaffold_format,
            project_root=project_root,
        )
        yield DefsPathSandbox(
            project_root=project_root,
            defs_folder_path=defs_folder_path,
            project_name=project_name,
            component_path=Path(component_path),
            component_format=scaffold_format,
        )
