from dagster import Definitions, asset
from dagster._utils.test.definitions import definitions


@definitions
def defs() -> Definitions:
    @asset
    def asset1(): ...

    return Definitions(assets=[asset1])
