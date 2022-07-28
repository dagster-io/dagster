from dagster import load_assets_from_modules


def test_asset_group():
    from docs_snippets.concepts.assets import asset_group

    assert len(load_assets_from_modules([asset_group])) == 2
