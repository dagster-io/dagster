import importlib.util
import sys
from types import ModuleType
from typing import List

import click
from dagster_managed_elements.types import ManagedElementDiff, ManagedElementReconciler

MODULE_NAME = "usercode"


def load_module(file_path: str) -> ModuleType:
    """
    Imports a Python module from a file path.
    https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    """
    spec = importlib.util.spec_from_file_location(MODULE_NAME, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)

    return module


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


def check(input_file: str) -> ManagedElementDiff:
    module = load_module(input_file)
    reconcilable_objects = get_reconcilable_objects(module)

    print(f"Found {len(reconcilable_objects)} stacks, checking...")

    diff = ManagedElementDiff()
    for obj in reconcilable_objects:
        diff = diff.join(obj.check())
    return diff


def apply(input_file: str) -> ManagedElementDiff:

    module = load_module(input_file)
    reconcilable_objects = get_reconcilable_objects(module)

    print(f"Found {len(reconcilable_objects)} stacks, applying...")

    diff = ManagedElementDiff()
    for obj in reconcilable_objects:
        diff = diff.join(obj.apply())
    return diff


@click.group()
def main():
    pass


@main.command(name="check")
@click.argument("input-file", type=click.Path(exists=True))
def check_cmd(input_file):
    print(check(input_file))


@main.command(name="apply")
@click.argument("input-file", type=click.Path(exists=True))
def apply_cmd(input_file):
    print(apply(input_file))
