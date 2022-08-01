from dagster._legacy import AssetGroup
from docs_snippets.guides.dagster.asset_tutorial import cereal
from docs_snippets.intro_tutorial.test_util import patch_cereal_requests


@patch_cereal_requests
def test_cereal():
    result = AssetGroup.from_modules([cereal]).materialize()
    assert result.success
