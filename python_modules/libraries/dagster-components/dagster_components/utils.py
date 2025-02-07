import importlib.util
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import click
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.errors import DagsterError

from dagster_components.core.schema.objects import AssetAttributesModel
from dagster_components.core.schema.resolver import TemplatedValueResolver

CLI_BUILTIN_COMPONENT_LIB_KEY = "builtin_component_lib"


def ensure_dagster_components_tests_import() -> None:
    from dagster_components import __file__ as dagster_components_init_py

    dagster_components_package_root = (Path(dagster_components_init_py) / ".." / "..").resolve()
    assert (
        dagster_components_package_root / "dagster_components_tests"
    ).exists(), "Could not find dagster_components_tests where expected"
    sys.path.append(dagster_components_package_root.as_posix())


def exit_with_error(error_message: str) -> None:
    click.echo(click.style(error_message, fg="red"))
    sys.exit(1)


# Temporarily places a path at the front of sys.path, ensuring that any modules in that path are
# importable.
@contextmanager
def ensure_loadable_path(path: Path) -> Iterator[None]:
    orig_path = sys.path.copy()
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path = orig_path


def get_path_for_package(package_name: str) -> str:
    spec = importlib.util.find_spec(package_name)
    if not spec:
        raise DagsterError(f"Cannot find package: {package_name}")
    # file_path = spec.origin
    submodule_search_locations = spec.submodule_search_locations
    if not submodule_search_locations:
        raise DagsterError(f"Package does not have any locations for submodules: {package_name}")
    return submodule_search_locations[0]


@dataclass
class ResolvingInfo:
    obj_name: str
    asset_attributes: AssetAttributesModel
    value_resolver: TemplatedValueResolver

    def get_asset_spec(self, base_spec: AssetSpec, context: Mapping[str, Any]) -> AssetSpec:
        """Returns an AssetSpec that combines the base spec with attributes resolved using the provided context.

        Usage:

        ```python
        class WrappedDagsterXTranslator(DagsterXTranslator):
            def __init__(self, *, base_translator, resolving_info: ResolvingInfo):
                self.base_translator = base_translator
                self.resolving_info = resolving_info

            def get_asset_spec(self, base_spec: AssetSpec, x_params: Any) -> AssetSpec:
                return self.resolving_info.get_asset_spec(
                    base_spec, {"x_params": x_params}
                )

        ```
        """
        resolver = self.value_resolver.with_scope(**context)
        resolved_attributes = self.asset_attributes.resolve(resolver)
        return base_spec.replace_attributes(**resolved_attributes)


def get_wrapped_translator_class(translator_type: type):
    """Temporary hack to allow wrapping of many methods of a given translator class. Will be removed
    once all translators implement `get_asset_spec`.
    """

    class WrappedTranslator(translator_type):
        def __init__(self, *, resolving_info: ResolvingInfo):
            self.base_translator = translator_type()
            self.resolving_info = resolving_info

        def get_asset_spec(self, obj: Any) -> AssetSpec:
            return self.resolving_info.get_asset_spec(
                self.base_translator.get_asset_spec(obj), {"obj": obj}
            )

    return WrappedTranslator


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
