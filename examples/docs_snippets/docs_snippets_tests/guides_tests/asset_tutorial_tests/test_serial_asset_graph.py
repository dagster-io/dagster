from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.module_loaders.load_assets_from_modules import (
    load_assets_from_modules,
)
from docs_snippets.guides.dagster.asset_tutorial import serial_asset_graph
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_serial_asset_graph():
    assets = load_assets_from_modules([serial_asset_graph])
    assert materialize(assets)
