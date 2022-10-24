import functools
import importlib
import sys
from types import ModuleType
from typing import List, Optional

import click
from dagster_managed_elements.types import ManagedElementDiff, ManagedElementReconciler


def _deepgetattr(obj, attr: str):
    """
    Recursive getattr that allows for nested attributes.
    https://stackoverflow.com/a/14324459
    """
    return functools.reduce(getattr, attr.split("."), obj)


def get_reconcilable_objects_from_module(
    module_dir: Optional[str], import_str: str
) -> List[ManagedElementReconciler]:
    module_str = import_str
    object_paths = None

    if ":" in module_str:
        module_str, obj_str = module_str.split(":", 1)
        object_paths = obj_str.split(",")

    if module_dir:
        sys.path.append(module_dir)

    try:
        module = importlib.import_module(module_str)
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


def get_reconcilable_objects(module: ModuleType) -> List[ManagedElementReconciler]:
    """
    Collect all ManagedElementReconciler-implementing objects in the root of the
    module.
    """
    return [
        getattr(module, obj)
        for obj in dir(module)
        if isinstance(getattr(module, obj), ManagedElementReconciler)
    ]


def check(module_dir: str, import_str: str) -> ManagedElementDiff:
    reconcilable_objects = get_reconcilable_objects_from_module(
        module_dir=module_dir, import_str=import_str
    )

    click.echo(f"Found {len(reconcilable_objects)} managed elements, checking...")

    diff = ManagedElementDiff()
    for obj in reconcilable_objects:
        result = obj.check()
        if isinstance(result, ManagedElementDiff):
            diff = diff.join(result)
        else:
            click.echo(result)
    return diff


def apply(module_dir: str, import_str: str) -> ManagedElementDiff:
    reconcilable_objects = get_reconcilable_objects_from_module(
        module_dir=module_dir, import_str=import_str
    )

    click.echo(f"Found {len(reconcilable_objects)} managed elements, applying...")

    diff = ManagedElementDiff()
    for obj in reconcilable_objects:
        result = obj.apply()
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
    help="Checks whether configuration for the specified managed elements is in sync with the current state, and prints a diff if not.",
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
def check_cmd(module, working_directory):
    click.echo(check(working_directory, module))


@main.command(
    name="apply",
    help="Reconciles the config for the specified managed elements, updating the remote state.",
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
def apply_cmd(module, working_directory):
    click.echo(apply(working_directory, module))
