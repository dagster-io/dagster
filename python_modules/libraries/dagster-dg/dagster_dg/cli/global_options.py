from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Any, Callable, Optional, TypeVar, Union

import click
import typer

from dagster_dg.config import DgConfig

T_Command = TypeVar("T_Command", bound=Union[Callable[..., Any], click.Command])

# Defaults are defined on the DgConfig object.
GLOBAL_OPTIONS = {
    option.name: option
    for option in [
        click.Option(
            ["--cache-dir"],
            type=Path,
            default=DgConfig.cache_dir,
            help="Specify a directory to use for the cache.",
        ),
        click.Option(
            ["--disable-cache"],
            is_flag=True,
            default=DgConfig.disable_cache,
            help="Disable the cache..",
        ),
        click.Option(
            ["--verbose"],
            is_flag=True,
            default=DgConfig.verbose,
            help="Enable verbose output for debugging.",
        ),
        click.Option(
            ["--builtin-component-lib"],
            type=str,
            default=DgConfig.builtin_component_lib,
            help="Specify a builitin component library to use.",
        ),
        click.Option(
            ["--use-dg-managed-environment/--no-use-dg-managed-environment"],
            is_flag=True,
            default=DgConfig.use_dg_managed_environment,
            help="Enable management of the virtual environment with uv.",
        ),
    ]
}


def typer_dg_global_options(
    cache_dir: Annotated[
        Path,
        typer.Option(
            help="Specify a directory to use for the cache.",
        ),
    ] = DgConfig.cache_dir,
    disable_cache: Annotated[
        bool,
        typer.Option(
            help="Disable the cache.",
        ),
    ] = DgConfig.disable_cache,
    verbose: Annotated[
        bool,
        typer.Option(
            help="Enable verbose output for debugging.",
        ),
    ] = DgConfig.verbose,
    builtin_component_lib: Annotated[
        str,
        typer.Option(
            help="Specify a builitin component library to use.",
        ),
    ] = DgConfig.builtin_component_lib,
    use_dg_managed_environment: Annotated[
        bool,
        typer.Option(
            help="Enable management of the virtual environment with uv.",
        ),
    ] = DgConfig.use_dg_managed_environment,
) -> dict[str, object]:
    return {
        "cache_dir": cache_dir,
        "disable_cache": disable_cache,
        "verbose": verbose,
        "builtin_component_lib": builtin_component_lib,
        "use_dg_managed_environment": use_dg_managed_environment,
    }


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
