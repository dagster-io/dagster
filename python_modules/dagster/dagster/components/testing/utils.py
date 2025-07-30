import importlib
import inspect
import json
import secrets
import shutil
import string
import sys
import textwrap
from pathlib import Path
from typing import Callable

import yaml
from dagster_shared import check

from dagster.components.component_scaffolding import scaffold_object
from dagster.components.core.component_tree import ComponentTree
from dagster.components.scaffold.scaffold import ScaffoldFormatOptions

"""Testing utilities for components."""

import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Optional, Union

from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import alter_sys_path
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.core.defs_module import CompositeYamlComponent, get_component


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
    context = context or ComponentTree.for_test().load_context
    return component.build_defs(context).with_resources(resources)


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
class DefsFolderSandbox:
    """A sandbox for testing components.

    This sandbox provides a number of utilities for scaffolding, modifying, and loading components
    from a temporary defs folder. This makes it easy to test components in isolation.
    """

    project_root: Path
    defs_folder_path: Path
    project_name: str

    @contextmanager
    def build_component_tree(self) -> Iterator[ComponentTree]:
        """Builds a ComponentTree from this sandbox's defs folder."""
        with alter_sys_path(to_add=[str(self.project_root / "src")], to_remove=[]):
            module_path = f"{self.project_name}.defs"
            try:
                tree = ComponentTree(
                    defs_module=importlib.import_module(module_path),
                    project_root=self.project_root,
                )
                yield tree

            finally:
                modules_to_remove = [name for name in sys.modules if name.startswith(module_path)]
                for name in modules_to_remove:
                    del sys.modules[name]

    @contextmanager
    def build_all_defs(self) -> Iterator[Definitions]:
        """Builds a Definitions object corresponding to all components in the sandbox.
        This is equivalent to what would be loaded from a real Dagster project with this
        sandbox's defs folder.
        """
        with self.build_component_tree() as tree:
            yield tree.build_defs()

    @contextmanager
    def load_component_and_build_defs(
        self, defs_path: Path
    ) -> Iterator[tuple[Component, Definitions]]:
        """Loads a Component object at the given path and builds the corresponding Definitions.

        Args:
            defs_path: The path to the component to load.

        Returns:
            A tuple of the Component and Definitions objects.

        Example:

        .. code-block:: python

            with scaffold_defs_sandbox() as sandbox:
                defs_path = sandbox.scaffold_component(component_cls=MyComponent)
                with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
                    component,
                    defs,
                ):
                    assert isinstance(component, MyComponent)
                    assert defs.get_asset_def("my_asset").key == AssetKey("my_asset")
        """
        with self.build_component_tree() as tree:
            component = tree.load_component_at_path(defs_path)
            defs = tree.build_defs_at_path(defs_path)
            yield component, defs

    def scaffold_component(
        self,
        component_cls: Any,
        defs_path: Optional[Union[Path, str]] = None,
        scaffold_params: Optional[dict[str, Any]] = None,
        scaffold_format: ScaffoldFormatOptions = "yaml",
        defs_yaml_contents: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Scaffolds a component into the defs folder.

        Args:
            component_cls: The component class to scaffold.
            defs_path: The path to the component. (defaults to a random name)
            scaffold_params: The parameters to pass to the scaffolder.
            scaffold_format: The format to use for scaffolding.
            defs_yaml_contents: The body of the component to update the defs.yaml file with.

        Returns:
            The path to the component.

        Example:

        .. code-block:: python

            with scaffold_defs_sandbox() as sandbox:
                defs_path = sandbox.scaffold_component(component_cls=MyComponent)
                assert (defs_path / "defs.yaml").exists()
        """
        defs_path = self.defs_folder_path / (defs_path or random_importable_name())
        typename = get_original_module_name(component_cls)
        scaffold_object(
            path=defs_path,
            typename=typename,
            json_params=json.dumps(scaffold_params) if scaffold_params else None,
            scaffold_format=scaffold_format,
            project_root=self.project_root,
        )
        if defs_yaml_contents:
            (defs_path / "defs.yaml").write_text(yaml.safe_dump(defs_yaml_contents))
        return defs_path

    @contextmanager
    def swap_defs_file(self, defs_path: Path, defs_yaml_contents: Optional[dict[str, Any]]):
        check.invariant(
            defs_path.suffix == ".yaml",
            "Attributes are only supported for yaml components",
        )
        check.invariant(defs_path.exists(), "defs.yaml must exist")

        # no need to override there is no component body
        if defs_yaml_contents is None:
            yield
            return

        temp_dir = Path(tempfile.mkdtemp())
        temp_path = temp_dir / defs_path.name

        try:
            shutil.copy2(defs_path, temp_path)

            defs_path.write_text(yaml.safe_dump(defs_yaml_contents))

            yield

        finally:
            if temp_path.exists():
                defs_path.unlink(missing_ok=True)
                shutil.copy2(temp_path, defs_path)
            shutil.rmtree(temp_dir)


@contextmanager
def create_defs_folder_sandbox(
    *,
    project_name: Optional[str] = None,
) -> Iterator[DefsFolderSandbox]:
    """Create a lightweight sandbox to scaffold and instantiate components. Useful
    for those authoring component types.

    Scaffold defs sandbox creates a temporary project that mimics the defs folder portion
    of a real dagster project. It then yields a DefsFolderSandbox object which can be used to
    scaffold and load components.

    DefsFolderSandbox has a few properties useful for different types of tests:

    * defs_folder_path: The absolute path to the defs folder. The user can inspect and
    load files from scaffolded components.
      e.g. (defs_folder_path / "my_component" / "defs.yaml").exists()

    * project_name: If not provided, a random name is generated.

    Once the sandbox is created the user has the option to load all definitions using the `load`
    method on DefsFolderSandbox, or the `load_component_at_path` mathod.

    This sandbox does not provide complete environmental isolation, but does provide some isolation guarantees
    to do its best to isolate the test from and restore the environment after the test.

    * A file structure like this is created: <<temp folder>> / src / <<project_name>> / defs
    * <<temp folder>> / src is placed in sys.path during the loading process
    * Any modules loaded during the process that descend from defs module are evicted from sys.modules on cleanup.

    Args:
        project_name: Optional name for the project (default: random name).

    Returns:
        Iterator[DefsFolderSandbox]: A context manager that yields a DefsFolderSandbox

    Example:

    .. code-block:: python

        with scaffold_defs_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(component_cls=MyComponent)
            assert (defs_path / "defs.yaml").exists()
            assert (defs_path / "my_component_config_file.yaml").exists()  # produced by MyComponentScaffolder

        with scaffold_defs_sandbox() as sandbox:
            defs_path = sandbox.scaffold_component(
                component_cls=MyComponent,
                defs_yaml_contents={"type": "MyComponent", "attributes": {"asset_key": "my_asset"}},
            )
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                assert isinstance(component, MyComponent)
                assert defs.get_asset_def("my_asset").key == AssetKey("my_asset")

    """
    project_name = project_name or random_importable_name()

    with tempfile.TemporaryDirectory() as project_root_str:
        project_root = Path(project_root_str)
        defs_folder_path = project_root / "src" / project_name / "defs"
        defs_folder_path.mkdir(parents=True, exist_ok=True)
        yield DefsFolderSandbox(
            project_root=project_root,
            defs_folder_path=defs_folder_path,
            project_name=project_name,
        )


def copy_code_to_file(fn: Callable, file_path: Path) -> None:
    """Takes a function and writes the body of the function to a file.

    Args:
        fn: The function to write to the file.
        file_path: The path to the file to write the function to.

    Example:

    .. code-block:: python

        def code_to_copy() -> None:
            import dagster as dg

            def execute_fn(context) -> dg.MaterializeResult:
                return dg.MaterializeResult()

        copy_code_to_file(code_to_copy, sandbox.defs_folder_path / "execute.py")
    """
    source_code_text = inspect.getsource(fn)
    source_code_text = "\n".join(source_code_text.split("\n")[1:])
    dedented_source_code_text = textwrap.dedent(source_code_text)
    file_path.write_text(dedented_source_code_text)
