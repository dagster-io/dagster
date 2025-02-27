import textwrap
from collections.abc import Sequence
from typing import Any, Callable, Optional, TypeVar, Union

import click

from dagster_dg.config import DgCliConfig
from dagster_dg.utils import set_option_help_output_group

T_Command = TypeVar("T_Command", bound=Union[Callable[..., Any], click.Command])

# Defaults are defined on the DgConfig object.
GLOBAL_OPTIONS = {
    option.name: option
    for option in [
        click.Option(
            ["--cache-dir"],
            default=str(DgCliConfig.cache_dir),
            help="Specify a directory to use for the cache.",
        ),
        click.Option(
            ["--disable-cache"],
            is_flag=True,
            default=DgCliConfig.disable_cache,
            help="Disable the cache..",
        ),
        click.Option(
            ["--verbose"],
            is_flag=True,
            default=DgCliConfig.verbose,
            help="Enable verbose output for debugging.",
        ),
        click.Option(
            ["--use-component-module", "use_component_modules"],
            type=str,
            multiple=True,
            default=DgCliConfig.__dataclass_fields__["use_component_modules"].default_factory(),
            hidden=True,
            help=textwrap.dedent("""
                Specify a list of remote environment modules expected to contain components.
                When retrieving the default set of components from the target environment, only
                components from these modules will be fetched. This overrides the default behavior
                of fetching all components registered under entry points in the remote environment.
                This is useful primarily for testing, as it allows targeting of a stable set of test
                components.
            """).strip(),
        ),
        click.Option(
            ["--use-dg-managed-environment/--no-use-dg-managed-environment"],
            is_flag=True,
            default=DgCliConfig.use_dg_managed_environment,
            help="Enable management of the virtual environment with uv.",
        ),
        click.Option(
            ["--require-local-venv/--no-require-local-venv"],
            is_flag=True,
            default=DgCliConfig.require_local_venv,
            help="Require use of a local virtual environment (`.venv` found in ancestors of the working directory).",
        ),
    ]
}

# Ensure that these options show up in the help output under the "Global options" group.
for option in GLOBAL_OPTIONS.values():
    set_option_help_output_group(option, "Global options")


def dg_global_options(
    fn: Optional[T_Command] = None, *, names: Optional[Sequence[str]] = None
) -> Union[T_Command, Callable[[T_Command], T_Command]]:
    if fn:
        options = [GLOBAL_OPTIONS[name] for name in names or list(GLOBAL_OPTIONS.keys())]
        if isinstance(fn, click.Command):
            for option in options:
                fn.params.append(option)
        else:
            # This is borrowed from click itself, it is how its decorators operate on both commands
            # and regular functions.
            if not hasattr(fn, "__click_params__"):
                fn.__click_params__ = []  # type: ignore
            for option in options:
                fn.__click_params__.append(option)  # type: ignore

        return fn
    else:
        return lambda fn: dg_global_options(fn, names=names)  # type: ignore


def validate_global_opts(context: click.Context, **global_options: object) -> None:
    for name, value in global_options.items():
        if name not in GLOBAL_OPTIONS:
            raise click.UsageError(f"Unknown global option: {name}")
        GLOBAL_OPTIONS[name].process_value(context, value)
