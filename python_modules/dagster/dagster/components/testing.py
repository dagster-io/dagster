import importlib
import inspect
import secrets
import shutil
import string
import sys
import textwrap
from pathlib import Path
from typing import Callable

import yaml
from dagster_shared import check
from dagster_shared.merger import deep_merge_dicts

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.partitions.definition import StaticPartitionsDefinition
from dagster.components.core.tree import ComponentTree

"""Testing utilities for components."""

import json
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, NamedTuple, Optional, Union

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

# Unfortunate hack - we only use this util in pytest tests, we just drop in a no-op
# implementation if pytest is not installed.
try:
    import pytest  # type: ignore
except ImportError:

    class pytest:
        @staticmethod
        def fixture(*args, **kwargs) -> Callable:
            def wrapper(fn):
                return fn

            return wrapper


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


def defs_from_component_yaml_path(
    *,
    component_yaml: Path,
    context: Optional[ComponentLoadContext] = None,
    resources: Optional[dict[str, Any]] = None,
):
    context = context or ComponentTree.for_test().load_context
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


class TranslationTestCase(NamedTuple):
    name: str
    attributes: dict[str, Any]
    assertion: Callable[[AssetSpec], bool]
    key_modifier: Optional[Callable[[AssetKey], AssetKey]] = None


test_cases = [
    TranslationTestCase(
        name="group_name",
        attributes={"group_name": "group"},
        assertion=lambda asset_spec: asset_spec.group_name == "group",
    ),
    TranslationTestCase(
        name="owners",
        attributes={"owners": ["team:analytics"]},
        assertion=lambda asset_spec: asset_spec.owners == ["team:analytics"],
    ),
    TranslationTestCase(
        name="tags",
        attributes={"tags": {"foo": "bar"}},
        assertion=lambda asset_spec: asset_spec.tags.get("foo") == "bar",
    ),
    TranslationTestCase(
        name="kinds",
        attributes={"kinds": ["snowflake", "dbt"]},
        assertion=lambda asset_spec: "snowflake" in asset_spec.kinds and "dbt" in asset_spec.kinds,
    ),
    TranslationTestCase(
        name="tags-and-kinds",
        attributes={"tags": {"foo": "bar"}, "kinds": ["snowflake", "dbt"]},
        assertion=lambda asset_spec: "snowflake" in asset_spec.kinds
        and "dbt" in asset_spec.kinds
        and asset_spec.tags.get("foo") == "bar",
    ),
    TranslationTestCase(
        name="code-version",
        attributes={"code_version": "1"},
        assertion=lambda asset_spec: asset_spec.code_version == "1",
    ),
    TranslationTestCase(
        name="description",
        attributes={"description": "some description"},
        assertion=lambda asset_spec: asset_spec.description == "some description",
    ),
    TranslationTestCase(
        name="metadata",
        attributes={"metadata": {"foo": "bar"}},
        assertion=lambda asset_spec: asset_spec.metadata.get("foo") == "bar",
    ),
    TranslationTestCase(
        name="deps",
        attributes={"deps": ["nonexistent"]},
        assertion=lambda asset_spec: len(asset_spec.deps) == 1
        and asset_spec.deps[0].asset_key == AssetKey("nonexistent"),
    ),
    TranslationTestCase(
        name="automation_condition",
        attributes={"automation_condition": "{{ automation_condition.eager() }}"},
        assertion=lambda asset_spec: asset_spec.automation_condition is not None,
    ),
    TranslationTestCase(
        name="key",
        attributes={"key": "{{ spec.key.to_user_string() + '_suffix' }}"},
        assertion=lambda asset_spec: asset_spec.key.path[-1].endswith("_suffix"),
        key_modifier=lambda key: AssetKey(path=list(key.path[:-1]) + [f"{key.path[-1]}_suffix"]),
    ),
    TranslationTestCase(
        name="key_prefix",
        attributes={"key_prefix": "cool_prefix"},
        assertion=lambda asset_spec: asset_spec.key.has_prefix(["cool_prefix"]),
        key_modifier=lambda key: AssetKey(path=["cool_prefix"] + list(key.path)),
    ),
    TranslationTestCase(
        name="partitions_defs",
        attributes={"partitions_def": {"type": "static", "partition_keys": ["foo", "bar"]}},
        assertion=lambda asset_spec: isinstance(
            asset_spec.partitions_def, StaticPartitionsDefinition
        ),
    ),
]


class TestTranslation:
    """Pytest test class for testing translation of asset attributes. You can subclass
    this class and implement a test_translation function using the various fixtures in
    order to comprehensively test asset translation options for your component.
    """

    @pytest.fixture(params=test_cases, ids=[case.name for case in test_cases])
    def translation_test_case(self, request):
        return request.param

    @pytest.fixture
    def attributes(self, translation_test_case: TranslationTestCase):
        return translation_test_case.attributes

    @pytest.fixture
    def assertion(self, translation_test_case: TranslationTestCase):
        return translation_test_case.assertion

    @pytest.fixture
    def key_modifier(self, translation_test_case: TranslationTestCase):
        return translation_test_case.key_modifier


class TestTranslationBatched(TestTranslation):
    """This version of the TestTranslation class is used to test the translation of
    asset attributes, applying all customizations in parallel to speed up tests for
    components which might be expensive to construct.
    """

    @pytest.fixture()
    def translation_test_case(self, request):
        deep_merge_all_attributes = {}
        for case in test_cases:
            deep_merge_all_attributes = deep_merge_dicts(deep_merge_all_attributes, case.attributes)
        merged_assertion = lambda asset_spec: all(case.assertion(asset_spec) for case in test_cases)

        # successively apply key modifiers
        def _merged_key_modifier(key):
            for case in test_cases:
                if case.key_modifier:
                    key = case.key_modifier(key)
            return key

        return TranslationTestCase(
            name="merged",
            attributes=deep_merge_all_attributes,
            assertion=merged_assertion,
            key_modifier=_merged_key_modifier,
        )


class TestOpCustomization:
    """Pytest test class for testing customization of op spec. You can subclass
    this class and implement a test_op_customization function using the various fixtures in
    order to comprehensively test op spec customization options for your component.
    """

    @pytest.fixture(
        params=[
            (
                {"name": "my_op"},
                lambda op: op.name == "my_op",
            ),
            (
                {"tags": {"foo": "bar"}},
                lambda op: op.tags.get("foo") == "bar",
            ),
            (
                {"backfill_policy": {"type": "single_run"}},
                lambda op: op.backfill_policy.max_partitions_per_run is None,
            ),
        ],
        ids=["name", "tags", "backfill_policy"],
    )
    def translation_test_case(self, request):
        return request.param

    @pytest.fixture
    def attributes(self, translation_test_case):
        return translation_test_case[0]

    @pytest.fixture
    def assertion(self, translation_test_case):
        return translation_test_case[1]
