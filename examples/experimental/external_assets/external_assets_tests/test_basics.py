import external_assets
from dagster import Definitions


def test_include():
    assert isinstance(external_assets.defs, Definitions)
