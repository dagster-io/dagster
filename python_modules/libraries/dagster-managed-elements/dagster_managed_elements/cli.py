import functools
import importlib
import logging
import sys
import warnings
from types import ModuleType
from typing import Optional, Sequence

import click
import click_spinner
from dagster_managed_elements.types import ManagedElementDiff, ManagedElementReconciler

from dagster._utils.backcompat import ExperimentalWarning


def _deepgetattr(obj, attr: str):
    """
    Recursive getattr that allows for nested attributes.
    https://stackoverflow.com/a/14324459
    """
    return functools.reduce(getattr, attr.split("."), obj)


def get_reconcilable_objects_from_module(
    module_dir: Optional[str], import_str: str
) -> Sequence[ManagedElementReconciler]:
    module_str = import_str
    object_paths = None

    if ":" in module_str:
        module_str, obj_str = module_str.split(":", 1)
        object_paths = obj_str.split(",")

    if module_dir:
        sys.path.append(module_dir)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)
            current_level = logging.getLogger().level
            logging.getLogger().setLevel(logging.ERROR)
            module = importlib.import_module(module_str)
            logging.getLogger().setLevel(current_level)
    except ModuleNotFoundError:
        raise ValueError(f"Could not import module {module_str}")

    if object_paths is None:
        object_paths = [
            obj for obj in dir(module) if isinstance(getattr(module, obj), ManagedElementReconciler)
        ]

    reconcilable_objects = [_deepgetattr(module, path) for path in object_paths]

    for entry in zip(object_paths, reconcilable_objects):
        path, obj = entry
        if not isinstance(obj, ManagedElementReconciler):
            raise ValueError(f"{module_str}:{path} is not a ManagedElementReconciler")

    return reconcilable_objects


def get_reconcilable_objects(module: ModuleType) -> Sequence[ManagedElementReconciler]:
    """
    Collect all ManagedElementReconciler-implementing objects in the root of the
    module.
    """
    return [
        getattr(module, obj)
        for obj in dir(module)
        if isinstance(getattr(module, obj), ManagedElementReconciler)
    ]


def check(module_dir: str, import_str: str, **kwargs) -> ManagedElementDiff:
    click.echo("Loading module...")
    with click_spinner.spinner():
        reconcilable_objects = get_reconcilable_objects_from_module(
            module_dir=module_dir, import_str=import_str
        )

    click.echo(f"Found {len(reconcilable_objects)} reconcilers, checking...")

    diff = ManagedElementDiff()
    for obj in reconcilable_objects:
        result = obj.check(**kwargs)
        if isinstance(result, ManagedElementDiff):
            diff = diff.join(result)
        else:
            click.echo(result)
    return diff


def apply(module_dir: str, import_str: str, **kwargs) -> ManagedElementDiff:
    reconcilable_objects = get_reconcilable_objects_from_module(
        module_dir=module_dir, import_str=import_str
    )

    click.echo(f"Found {len(reconcilable_objects)} reconcilers, applying...")

    diff = ManagedElementDiff()
    for obj in reconcilable_objects:
        result = obj.apply(**kwargs)
        if isinstance(result, ManagedElementDiff):
            diff = diff.join(result)
        else:
            click.echo(result)
    return diff


@click.group()
def main():
    pass


@main.command(
    name="check",
    help="Checks whether configuration for the specified reconcilers are in sync with the current state, and prints a diff if not.",
)
@click.option(
    "--module",
    "-m",
    type=str,
    required=True,
    help="Module containing the reconcilers to check.\nOptionally can include a colon and a comma-separated list of attribute paths to check specific reconcilers, otherwise all reconcilers in the module root will be checked, e.g. `my_module:reconciler1,reconciler2`",
)
@click.option(
    "--working-directory",
    "-d",
    type=click.Path(exists=True),
    help="Optional relative or absolute path to load module from, will be appended to system path.",
)
@click.option(
    "--include-all-secrets",
    is_flag=True,
    help=(
        "Whether to include all secrets in the diff, acting as if all secrets will be pushed to the remote state."
        " Secrets cannot be retrieved and diffed against the remote state, so this option simulates the diff if this flag is included to the apply command."
    ),
)
def check_cmd(module, working_directory, include_all_secrets):
    diff = check(working_directory, module, include_all_secrets=include_all_secrets)

    if diff.is_empty():
        click.echo(click.style("\nNo diff found.", fg="green"))
    else:
        click.echo(click.style("\nChanges found:", fg="yellow"))
        click.echo(diff)


@main.command(
    name="apply",
    help="Reconciles the config for the specified reconcilers, updating the remote state.",
)
@click.option(
    "--module",
    "-m",
    type=str,
    required=True,
    help="Module containing the reconcilers to apply.\nOptionally can include a colon and a comma-separated list of attribute paths to apply specific reconcilers, otherwise all reconcilers in the module root will be checked, e.g. `my_module:reconciler1,reconciler2`",
)
@click.option(
    "--working-directory",
    "-d",
    type=click.Path(exists=True),
    help="Optional relative or absolute path to load module from, will be appended to system path.",
)
@click.option(
    "--include-all-secrets",
    is_flag=True,
    help=(
        "Whether to push all secret values to the remote state, or only those that aren't already present."
        " Secrets cannot be retrieved and diffed against the remote state, so this option is required when a secret is changed."
        " If False, secrets that are already present in the remote state will not be pushed."
    ),
)
def apply_cmd(module, working_directory, include_all_secrets):
    diff = apply(working_directory, module, include_all_secrets=include_all_secrets)

    if diff.is_empty():
        click.echo(click.style("\nNo changes applied.", fg="green"))
    else:
        click.echo(click.style("\nChanges applied:", fg="yellow"))
        click.echo(diff)
