import sys
from dataclasses import dataclass
from pathlib import Path

import click
from typing_extensions import Self

from dagster_dg.error import DgError

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
    def from_cli_context(cls, cli_context: click.Context) -> Self:
        if _CLI_CONTEXT_CONFIG_KEY not in cli_context.obj:
            raise DgError(
                "Attempted to extract DgConfig from CLI context but nothing stored under designated key `{_CLI_CONTEXT_CONFIG_KEY}`."
            )
        return cli_context.obj[_CLI_CONTEXT_CONFIG_KEY]

    @classmethod
    def default(cls) -> "DgConfig":
        return cls()


_CLI_CONTEXT_CONFIG_KEY = "config"


def set_config_on_cli_context(cli_context: click.Context, config: DgConfig) -> None:
    cli_context.ensure_object(dict)
    cli_context.obj[_CLI_CONTEXT_CONFIG_KEY] = config
