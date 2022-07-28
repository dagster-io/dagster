from dagster._legacy import AssetGroup
from docs_snippets.guides.dagster.asset_tutorial import serial_asset_graph
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_serial_asset_graph():
    result = AssetGroup.from_modules([serial_asset_graph]).materialize()
    assert result.success
