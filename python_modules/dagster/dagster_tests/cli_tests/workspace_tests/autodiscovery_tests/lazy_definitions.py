from dagster import Definitions, asset
from dagster._utils.test.definitions import lazy_definitions


@lazy_definitions
def defs() -> Definitions:
    @asset
    def asset1(): ...

    return Definitions(assets=[asset1])
