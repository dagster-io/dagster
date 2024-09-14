from dagster import Definitions, asset
from dagster._core.definitions.decorators.definitions_decorator import definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext


@definitions
def defs(context: DefinitionsLoadContext) -> Definitions:
    @asset
    def asset1(): ...

    return Definitions(assets=[asset1])
