import importlib.util
import subprocess
import sys
import textwrap
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, TypeVar

import click
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.tags import build_kind_tag
from dagster._core.errors import DagsterError

from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.objects import (
    AssetAttributesSchema,
    resolve_asset_attributes_to_mapping,
)

T = TypeVar("T")


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


def format_error_message(message: str) -> str:
    # width=10000 unwraps any hardwrapping
    dedented = textwrap.dedent(message).strip()
    paragraphs = [textwrap.fill(p, width=10000) for p in dedented.split("\n\n")]
    return "\n\n".join(paragraphs)


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
class TranslatorResolvingInfo:
    obj_name: str
    asset_attributes: AssetAttributesSchema
    resolution_context: ResolutionContext

    def get_resolved_attribute(self, attribute: str, obj: Any, default_method) -> Any:
        resolved_attributes = resolve_asset_attributes_to_mapping(
            context=self.resolution_context.with_scope(**{self.obj_name: obj}),
            schema=self.asset_attributes,
        )

        return (
            resolved_attributes[attribute]
            if attribute in resolved_attributes
            else default_method(obj)
        )

    def merge_resolved_dict_attribute(
        self, attribute: str, obj: Any, default_method
    ) -> Mapping[str, Any]:
        """Merges a resolved attribute with the dict from the underlying translator.

        This is useful for allowing users to augment the translator's dict with additional
        values, instead of replacing the dict entirely.
        """
        attribute_value = dict(default_method(obj) or {})

        resolved_attributes = resolve_asset_attributes_to_mapping(
            context=self.resolution_context.with_scope(**{self.obj_name: obj}),
            schema=self.asset_attributes,
        )

        if attribute in resolved_attributes:
            attribute_value.update(resolved_attributes[attribute])
        return attribute_value

    def get_asset_spec(self, base_spec: AssetSpec, context: Mapping[str, Any]) -> AssetSpec:
        """Returns an AssetSpec that combines the base spec with attributes resolved using the provided context.

        Usage:

        ```python
        class WrappedDagsterXTranslator(DagsterXTranslator):
            def __init__(self, *, base_translator, resolving_info: TranslatorResolvingInfo):
                self.base_translator = base_translator
                self.resolving_info = resolving_info

            def get_asset_spec(self, base_spec: AssetSpec, x_params: Any) -> AssetSpec:
                return self.resolving_info.get_asset_spec(
                    base_spec, {"x_params": x_params}
                )

        ```
        """
        resolved_attributes = resolve_asset_attributes_to_mapping(
            schema=self.asset_attributes,
            context=self.resolution_context.with_scope(**context),
        )
        return base_spec.replace_attributes(**resolved_attributes)


def get_wrapped_translator_class(translator_type: type):
    """Temporary hack to allow wrapping of many methods of a given translator class. Will be removed
    once all translators implement `get_asset_spec`.
    """

    class WrappedTranslator(translator_type):
        def __init__(self, *, resolving_info: TranslatorResolvingInfo):
            self.base_translator = translator_type()
            self.resolving_info = resolving_info

        def get_asset_key(self, obj: Any) -> AssetKey:
            return self.resolving_info.get_resolved_attribute(
                "key", obj, self.base_translator.get_asset_key
            )

        def get_group_name(self, obj: Any) -> Optional[str]:
            return self.resolving_info.get_resolved_attribute(
                "group_name", obj, self.base_translator.get_group_name
            )

        def get_tags(self, obj: Any) -> Mapping[str, str]:
            tags = {}

            base_kinds = (
                self.base_translator.get_kinds
                if hasattr(self.base_translator, "get_kinds")
                else lambda *args: []
            )
            kinds = self.resolving_info.get_resolved_attribute("kinds", obj, base_kinds)
            for kind in kinds:
                tags.update(build_kind_tag(kind))

            tags.update(
                self.resolving_info.merge_resolved_dict_attribute(
                    "tags", obj, self.base_translator.get_tags
                )
            )
            return tags

        def get_automation_condition(self, obj: Any) -> Optional[AutomationCondition]:
            return self.resolving_info.get_resolved_attribute(
                "automation_condition",
                obj,
                self.base_translator.get_automation_condition,
            )

        def get_metadata(self, obj: Any) -> Mapping[str, Any]:
            return self.resolving_info.merge_resolved_dict_attribute(
                "metadata", obj, self.base_translator.get_metadata
            )

        def get_owners(self, obj: Any) -> Sequence[str]:
            return self.resolving_info.get_resolved_attribute(
                "owners", obj, self.base_translator.get_owners
            )

        def get_code_version(self, obj: Any) -> Optional[str]:
            version = self.resolving_info.get_resolved_attribute(
                "code_version", obj, self.base_translator.get_code_version
            )
            return str(version) if version else None

        def get_description(self, obj: Any) -> Optional[str]:
            return self.resolving_info.get_resolved_attribute(
                "description", obj, self.base_translator.get_description
            )

        def get_deps_asset_key(self, obj: Any) -> Iterable[AssetKey]:
            return [
                AssetKey.from_user_string(dep) if isinstance(dep, str) else dep
                for dep in self.resolving_info.get_resolved_attribute(
                    "deps", obj, self.base_translator.get_deps_asset_key
                )
            ]

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


# ########################
# ##### PLATFORM
# ########################


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"


# ########################
# ##### VENV
# ########################


def get_venv_executable(venv_dir: Path, executable: str = "python") -> Path:
    if is_windows():
        return venv_dir / "Scripts" / f"{executable}.exe"
    else:
        return venv_dir / "bin" / executable


def install_to_venv(venv_dir: Path, install_args: list[str]) -> None:
    executable = get_venv_executable(venv_dir)
    command = ["uv", "pip", "install", "--python", str(executable), *install_args]
    subprocess.run(command, check=True)
