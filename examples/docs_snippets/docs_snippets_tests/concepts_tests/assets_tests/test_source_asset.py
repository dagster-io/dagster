from dagster import repository
from docs_snippets.concepts.assets.source_asset import my_derived_asset, my_source_asset


def test_source_asset():
    @repository
    def repo():
        return [my_source_asset, my_derived_asset]

    assert my_derived_asset([5]) == [5, 4]
