from dagster import Definitions, ResourceParam, asset

# from some_file import some_asset  # does not work
# E   ModuleNotFoundError: No module named 'some_file'
# from .some_file import some_asset  # does not work
# E   ImportError: attempted relative import with no known parent package
from dagster_components_tests.integration_tests.components.definitions.definitions_object.some_file import (
    some_asset,
)


class SomeResource: ...


@asset
def an_asset(some_resource: ResourceParam[SomeResource]) -> None: ...


defs = Definitions([an_asset, some_asset], resources={"some_resource": SomeResource()})
