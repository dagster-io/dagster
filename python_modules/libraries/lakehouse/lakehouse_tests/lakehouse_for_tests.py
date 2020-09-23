from lakehouse import Lakehouse, computed_asset
from lakehouse_tests.conftest import DictStorage

from dagster import ModeDefinition, resource


@computed_asset()
def asset1():
    pass


@computed_asset(input_assets=[asset1])
def asset2(_):
    pass


@resource()
def a_storage(_):
    return DictStorage()


lakehouse_def = Lakehouse(
    mode_defs=[ModeDefinition(name="dev", resource_defs={"default_storage": a_storage})],
    assets=[asset1, asset2],
)
