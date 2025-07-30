import importlib
import json
import shutil
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

import yaml
from dagster_shared import check

from dagster._annotations import deprecated
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils import alter_sys_path
from dagster.components.component.component import Component
from dagster.components.component_scaffolding import scaffold_object
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.defs_module import CompositeYamlComponent, get_component
from dagster.components.scaffold.scaffold import ScaffoldFormatOptions


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
            module_path = get_module_path(
                defs_module_name=f"{self.project_name}.defs", component_path=self.component_path
            )
            try:
                yield get_all_components_defs_from_defs_path(
                    project_root=self.project_root,
                    module_path=module_path,
                )

            finally:
                modules_to_remove = [name for name in sys.modules if name.startswith(module_path)]
                for name in modules_to_remove:
                    del sys.modules[name]


@deprecated(
    additional_warn_text="Use dagster.components.testing.create_defs_folder_sandbox instead.",
    breaking_version="2.0.0",
)
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
            with sandbox.load(defs_yaml_contents={"type": "MyComponent", "attributes": {"asset_key": "different_asset_key"}}) as (component, defs):
                assert isinstance(component, MyComponent)
                assert defs.get_asset_def("different_asset_key").key == AssetKey("different_asset_key")
    """
    from dagster.components.testing.utils import get_original_module_name, random_importable_name

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


@deprecated(
    breaking_version="2.0.0",
)
def get_module_path(defs_module_name: str, component_path: Path):
    component_module_path = str(component_path).replace("/", ".")
    return f"{defs_module_name}.{component_module_path}"


def flatten_components(parent_component: Optional[Component]) -> list[Component]:
    if isinstance(parent_component, CompositeYamlComponent):
        return list(parent_component.components)
    elif isinstance(parent_component, Component):
        return [parent_component]
    else:
        return []


@deprecated(
    breaking_version="2.0.0",
    additional_warn_text="Use dagster.ComponentTree.for_project instead.",
)
def get_component_defs_within_project(
    *,
    project_root: Union[str, Path],
    component_path: Union[str, Path],
    instance_key: int = 0,
) -> tuple[Component, Definitions]:
    """Get the component defs for a component within a project. This only works if dagster_dg_core is installed.

    Args:
        project_root: The root of the project.
        component_path: The path to the component.

    Returns:
        A tuple of the component and its definitions.
    """
    all_component_defs = get_all_components_defs_within_project(
        project_root=project_root, component_path=component_path
    )
    return all_component_defs[instance_key][0], all_component_defs[instance_key][1]


@deprecated(
    breaking_version="2.0.0",
    additional_warn_text="Use dagster.ComponentTree.for_project instead.",
)
def get_all_components_defs_within_project(
    *,
    project_root: Union[str, Path],
    component_path: Union[str, Path],
) -> list[tuple[Component, Definitions]]:
    """Get all the component defs for a component within a project. This only works if dagster_dg_core is installed.

    Args:
        project_root: The root of the project.
        component_path: The path to the component.

    Returns:
        A list of tuples of the component and its definitions.
    """
    try:
        from dagster_dg_core.config import discover_config_file
        from dagster_dg_core.context import DgContext
    except ImportError:
        raise Exception(
            "dagster_dg_core is not installed. Please install it to use default project_name and defs module from pyproject.toml or dg.toml."
        )

    project_root = Path(project_root)
    component_path = Path(component_path)

    dg_context = DgContext.from_file_discovery_and_command_line_config(
        path=check.not_none(discover_config_file(project_root), "No project config file found."),
        command_line_config={},
    )

    return get_all_components_defs_from_defs_path(
        module_path=get_module_path(dg_context.defs_module_name, component_path),
        project_root=project_root,
    )


@deprecated(
    breaking_version="2.0.0",
    additional_warn_text="Use dagster.ComponentTree.for_project instead.",
)
def get_all_components_defs_from_defs_path(
    *,
    module_path: str,
    project_root: Union[str, Path],
) -> list[tuple[Component, Definitions]]:
    module = importlib.import_module(module_path)
    context = ComponentTree(
        defs_module=module,
        project_root=Path(project_root),
    ).load_context
    components = flatten_components(get_component(context))
    return [(component, component.build_defs(context)) for component in components]


@deprecated(
    breaking_version="2.0.0",
    additional_warn_text="Use dagster.ComponentTree.for_project instead.",
)
def get_component_defs_from_defs_path(
    *, module_path: str, project_root: Union[str, Path]
) -> tuple[Component, Definitions]:
    components = get_all_components_defs_from_defs_path(
        project_root=project_root,
        module_path=module_path,
    )
    check.invariant(
        len(components) == 1,
        "Only one component is supported. To get all components use get_all_components_defs_from_defs_path.",
    )
    return components[0]
