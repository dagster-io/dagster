from dataclasses import dataclass

import click
from typing_extensions import Self

from dagster_dg.error import DgError

DEFAULT_BUILTIN_COMPONENT_LIB = "dagster_components"


@dataclass
class DgConfig:
    """Global configuration for Dg.

    Attributes:
        builitin_component_lib (str): The name of the builtin component library to load.
    """

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
