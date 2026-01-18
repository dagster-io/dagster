import os
import textwrap
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

import click

from dagster_dg_core.config import DgCliConfig
from dagster_dg_core.utils import not_none, set_option_help_output_group

T_Command = TypeVar("T_Command", bound=Union[Callable[..., Any], click.Command])

# ########################
# ##### HELPERS
# ########################


def make_option_group(
    options_dict: dict[str, click.Option],
) -> Callable[..., Union[T_Command, Callable[[T_Command], T_Command]]]:
    def option_group(
        fn: Optional[T_Command] = None, *, names: Optional[Sequence[str]] = None
    ) -> Union[T_Command, Callable[[T_Command], T_Command]]:
        if fn:
            options = [options_dict[name] for name in names or list(options_dict.keys())]
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
            return lambda fn: option_group(fn, names=names)  # type: ignore

    return option_group


# ########################
# ##### GLOBAL
# ########################

# Defaults are defined on the DgConfig object.
GLOBAL_OPTIONS = {
    not_none(option.name): option
    for option in [
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
    ]
}

# Ensure that these options show up in the help output under the "Global options" group.
for option in GLOBAL_OPTIONS.values():
    set_option_help_output_group(option, "Global options")

dg_global_options = make_option_group(GLOBAL_OPTIONS)

# ########################
# ##### EDITABLE DAGSTER
# ########################

# When set, this will cause project scaffolding to default to --use-editable-dagster mode.
# This is a private feature designed to prevent mistakes during development.
DEFAULT_EDITABLE_DAGSTER_PROJECTS_ENV_VAR = "DG_USE_EDITABLE_DAGSTER"


# Returns false if the environment variable is not set or is set to "false".
def is_use_editable_env_var_true() -> bool:
    env_var_value = os.getenv(DEFAULT_EDITABLE_DAGSTER_PROJECTS_ENV_VAR)
    if not env_var_value:
        return False

    return env_var_value != "false"


EDITABLE_DAGSTER_OPTIONS = {
    not_none(option.name): option
    for option in [
        click.Option(
            ["--use-editable-dagster"],
            is_flag=True,
            default=True if is_use_editable_env_var_true() else False,
            help=(
                "Install all Dagster package dependencies from a local Dagster clone. The location "
                "of the local Dagster clone will be read from the `DAGSTER_GIT_REPO_DIR` environment variable."
            ),
        ),
    ]
}

dg_editable_dagster_options = make_option_group(EDITABLE_DAGSTER_OPTIONS)

PATH_OPTIONS = {
    not_none(option.name): option
    for option in [
        click.Option(
            ["--target-path"],
            type=click.Path(
                resolve_path=True,
                path_type=Path,
            ),
            help="Specify a directory to use to load the context for this command. This will typically be a folder with a dg.toml or pyproject.toml file in it.",
            default=lambda: Path.cwd(),  # defer for tests
        ),
    ]
}

dg_path_options = make_option_group(PATH_OPTIONS)

VENV_OPTIONS = {
    not_none(option.name): option
    for option in [
        click.Option(
            ["--use-active-venv"],
            type=click.BOOL,
            is_flag=True,
            default=False,
            help=(
                "Use the active virtual environment as defined by $VIRTUAL_ENV for all projects "
                "instead of attempting to resolve individual project virtual environments."
            ),
        ),
    ]
}

dg_venv_options = make_option_group(VENV_OPTIONS)
