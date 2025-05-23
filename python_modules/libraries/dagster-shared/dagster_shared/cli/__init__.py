from collections.abc import Sequence
from typing import Any, Callable, TypeVar

import click
from typing_extensions import TypeAlias

T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])

ClickOption: TypeAlias = Callable[[T_Callable], T_Callable]


def apply_click_params(command: T_Callable, *click_params: ClickOption) -> T_Callable:
    for click_param in click_params:
        command = click_param(command)
    return command


def python_pointer_options(f: T_Callable) -> T_Callable:
    return apply_click_params(f, *generate_python_pointer_options(allow_multiple=False))


def generate_python_pointer_options(allow_multiple: bool) -> Sequence[ClickOption]:
    return [
        click.option(
            "--working-directory",
            "-d",
            help="Specify working directory to use when loading the repository or job",
            envvar="DAGSTER_WORKING_DIRECTORY",
        ),
        click.option(
            "--python-file",
            "-f",
            # Checks that the path actually exists lower in the stack, where we
            # are better equipped to surface errors
            type=click.Path(exists=False),
            multiple=allow_multiple,
            help=(
                "Specify python file "
                + ("or files (flag can be used multiple times) " if allow_multiple else "")
                + "where dagster definitions reside as top-level symbols/variables and load "
                + ("each" if allow_multiple else "the")
                + " file as a code location in the current python environment."
            ),
            envvar="DAGSTER_PYTHON_FILE",
        ),
        click.option(
            "--module-name",
            "-m",
            multiple=allow_multiple,
            help=(
                "Specify module "
                + ("or modules (flag can be used multiple times) " if allow_multiple else "")
                + "where dagster definitions reside as top-level symbols/variables and load "
                + ("each" if allow_multiple else "the")
                + " module as a code location in the current python environment."
            ),
            envvar="DAGSTER_MODULE_NAME",
        ),
        click.option(
            "--package-name",
            multiple=allow_multiple,
            help="Specify Python package where repository or job function lives",
            envvar="DAGSTER_PACKAGE_NAME",
        ),
        click.option(
            "--attribute",
            "-a",
            help=(
                "Attribute that is either a 1) repository or job or "
                "2) a function that returns a repository or job"
            ),
            envvar="DAGSTER_ATTRIBUTE",
        ),
    ]
