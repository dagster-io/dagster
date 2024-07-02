from dagster import materialize, load_assets_from_modules
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests
from docs_snippets.guides.dagster.asset_tutorial import complex_asset_graph


@patch_cereal_requests
def test_complex_asset_graph():
    result = materialize(load_assets_from_modules([complex_asset_graph]))
    assert result.success
