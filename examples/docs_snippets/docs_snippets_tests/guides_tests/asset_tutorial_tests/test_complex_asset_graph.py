from dagster import AssetGroup
from docs_snippets.guides.dagster.asset_tutorial import complex_asset_graph
from docs_snippets.guides.dagster.asset_tutorial.complex_asset_graph_tests import (  # pylint: disable=unused-import
    test_cereal_asset_group,
    test_nabisco_cereals,
)
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_complex_asset_graph():
    result = AssetGroup.from_modules([complex_asset_graph]).materialize()
    assert result.success
