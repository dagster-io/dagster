from types import ModuleType
from typing import List
import click


import importlib.util
import sys

from dagster_managed_stacks.types import ManagedStackDiff, ManagedStackReconciler

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


def get_reconcilable_objects(module: ModuleType) -> List[ManagedStackReconciler]:
    """
    Collect all ManagedStackReconciler-implementing objects in the root of the
    module.
    """
    return [
        getattr(module, obj)
        for obj in dir(module)
        if isinstance(getattr(module, obj), ManagedStackReconciler)
    ]


@click.group()
def main():
    pass


@main.command()
@click.argument("input-file", type=click.Path(exists=True))
def check(input_file):
    module = load_module(input_file)
    reconcilable_objects = get_reconcilable_objects(module)

    print(f"Found {len(reconcilable_objects)} stacks, checking...")

    diff = ManagedStackDiff()
    for obj in reconcilable_objects:
        diff = diff.join(obj.check())
    print(diff)


@main.command()
@click.argument("input-file", type=click.Path(exists=True))
def apply(input_file):
    module = load_module(input_file)
    reconcilable_objects = get_reconcilable_objects(module)

    print(f"Found {len(reconcilable_objects)} stacks, applying...")

    diff = ManagedStackDiff()
    for obj in reconcilable_objects:
        diff = diff.join(obj.apply())
    print(diff)
