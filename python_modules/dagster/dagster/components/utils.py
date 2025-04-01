import importlib.util
import subprocess
import sys
import textwrap
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, TypeVar, Union

import click
from pydantic import BaseModel

from dagster import _check as check
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.errors import DagsterError
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import (
    AssetAttributesModel,
    resolve_asset_attributes_to_mapping,
)

T = TypeVar("T")


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


TRANSLATOR_MERGE_ATTRIBUTES = {"metadata", "tags"}


@dataclass
class TranslatorResolvingInfo:
    obj_name: str
    asset_attributes: Union[str, BaseModel]
    resolution_context: ResolutionContext

    def _resolve_asset_attributes(self, context: Mapping[str, Any]) -> Union[AssetSpec, BaseModel]:
        """Resolves the user-specified asset attributes into an AssetAttributesModel, or an AssetSpec
        if the UDF returns one.
        """
        if not isinstance(self.asset_attributes, str):
            return self.asset_attributes

        resolved_asset_attributes = (
            self.resolution_context.at_path("asset_attributes")
            .with_scope(**context)
            .resolve_value(self.asset_attributes)
        )

        if isinstance(resolved_asset_attributes, AssetSpec):
            return resolved_asset_attributes
        elif isinstance(resolved_asset_attributes, AssetAttributesModel):
            return resolved_asset_attributes
        elif isinstance(resolved_asset_attributes, dict):
            return AssetAttributesModel(**(resolved_asset_attributes))
        else:
            check.failed(
                f"Unexpected return value for asset_attributes UDF: {type(resolved_asset_attributes)}"
            )

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
        resolved_asset_attributes = self._resolve_asset_attributes(context)
        if isinstance(resolved_asset_attributes, AssetSpec):
            return resolved_asset_attributes

        resolved_attributes = resolve_asset_attributes_to_mapping(
            model=resolved_asset_attributes,
            context=self.resolution_context.at_path("asset_attributes").with_scope(**context),
        )
        if "code_version" in resolved_attributes:
            resolved_attributes = {
                **resolved_attributes,
                "code_version": str(resolved_attributes["code_version"]),
            }
        return base_spec.replace_attributes(
            **{k: v for k, v in resolved_attributes.items() if k not in TRANSLATOR_MERGE_ATTRIBUTES}
        ).merge_attributes(
            **{k: v for k, v in resolved_attributes.items() if k in TRANSLATOR_MERGE_ATTRIBUTES}
        )


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


def get_path_from_module(module: ModuleType) -> Path:
    module_path = (
        Path(module.__file__).parent
        if module.__file__
        else Path(module.__path__[0])
        if module.__path__
        else None
    )
    return check.not_none(module_path, f"Module {module.__name__} has no filepath")
