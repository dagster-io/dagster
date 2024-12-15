from dagster._core.definitions.load_assets_from_modules import load_assets_from_modules
from dagster._core.definitions.materialize import materialize
from docs_snippets.guides.dagster.asset_tutorial import cereal
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_cereal():
    assets, source_assets, _ = load_assets_from_modules([cereal])
    assert materialize([*assets, *source_assets])
