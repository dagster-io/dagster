from dagster import load_assets_from_modules, materialize
from docs_snippets.guides.dagster.asset_tutorial import non_argument_deps
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_complex_asset_graph():
    result = materialize(load_assets_from_modules([non_argument_deps]))
    assert result.success
