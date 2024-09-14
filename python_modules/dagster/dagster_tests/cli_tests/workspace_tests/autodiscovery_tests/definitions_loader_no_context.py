from dagster import Definitions, asset
from dagster._core.definitions.decorators.definitions_decorator import definitions


@definitions
def defs() -> Definitions:
    @asset
    def asset1(): ...

    return Definitions(assets=[asset1])
