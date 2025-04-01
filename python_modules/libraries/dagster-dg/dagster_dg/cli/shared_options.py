import os
import textwrap
from collections.abc import Sequence
from typing import Any, Callable, Optional, TypeVar, Union

import click

from dagster_dg.config import DgCliConfig
from dagster_dg.utils import not_none, set_option_help_output_group

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
            type=str,
            flag_value="TRUE",
            is_flag=False,
            default="TRUE" if is_use_editable_env_var_true() else None,
            help=(
                "Install all Dagster package dependencies from a local Dagster clone. Accepts a path to local Dagster clone root or"
                " may be set as a flag (no value is passed). If set as a flag,"
                " the location of the local Dagster clone will be read from the `DAGSTER_GIT_REPO_DIR` environment variable."
            ),
        ),
    ]
}

dg_editable_dagster_options = make_option_group(EDITABLE_DAGSTER_OPTIONS)
