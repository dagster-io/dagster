import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Type, TypeVar

import click
from typing_extensions import Self

from dagster_dg.error import DgError

T = TypeVar("T")

DEFAULT_BUILTIN_COMPONENT_LIB = "dagster_components"


def _get_default_cache_dir() -> Path:
    if sys.platform == "win32":
        return Path.home() / "AppData" / "dg" / "cache"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "dg"
    else:
        return Path.home() / ".cache" / "dg"


DEFAULT_CACHE_DIR = _get_default_cache_dir()


@dataclass
class DgConfig:
    """Global configuration for Dg.

    Attributes:
        disable_cache (bool): If True, disable caching. Defaults to False.
        cache_dir (Optional[str]): The directory to use for caching. If None, the default cache will
            be used.
        verbose (bool): If True, log debug information.
        builitin_component_lib (str): The name of the builtin component library to load.
    """

    disable_cache: bool = False
    cache_dir: Path = DEFAULT_CACHE_DIR
    verbose: bool = False
    builtin_component_lib: str = DEFAULT_BUILTIN_COMPONENT_LIB

    @classmethod
    def from_cli_global_options(cls, global_options: Mapping[str, object]) -> Self:
        return cls(
            disable_cache=_validate_global_option(global_options, "disable_cache", bool),
            cache_dir=_validate_global_option(global_options, "cache_dir", Path),
            verbose=_validate_global_option(global_options, "verbose", bool),
            builtin_component_lib=_validate_global_option(
                global_options, "builtin_component_lib", str
            ),
        )

    @classmethod
    def default(cls) -> "DgConfig":
        return cls()


# This validation will generally already be done by click, but this internal validation routine
# provides insurance and satisfies the type checker.
def _validate_global_option(
    global_options: Mapping[str, object], key: str, expected_type: Type[T]
) -> T:
    value = global_options.get(key, getattr(DgConfig, key))
    if not isinstance(value, expected_type):
        raise DgError(f"Global option {key} must be of type {expected_type}.")
    return value


_CLI_CONTEXT_CONFIG_KEY = "config"


def set_config_on_cli_context(cli_context: click.Context, config: DgConfig) -> None:
    cli_context.ensure_object(dict)
    cli_context.obj[_CLI_CONTEXT_CONFIG_KEY] = config


def has_config_on_cli_context(cli_context: click.Context) -> bool:
    return _CLI_CONTEXT_CONFIG_KEY in cli_context.ensure_object(dict)


def get_config_from_cli_context(cli_context: click.Context) -> DgConfig:
    cli_context.ensure_object(dict)
    return cli_context.obj[_CLI_CONTEXT_CONFIG_KEY]
