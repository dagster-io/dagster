from dagster import AssetKey
from docs_snippets.concepts.assets.subset_graph_backed_asset import my_repo


def test_subset_graph_backed_asset():
    result = my_repo.get_job("graph_asset").execute_in_process(
        asset_selection=[AssetKey("baz_asset")]
    )
    assert result.success
    asset_materializations = [
        event for event in result.all_events if event.is_step_materialization
    ]
    assert len(asset_materializations) == 1
    assert asset_materializations[0].asset_key == AssetKey("baz_asset")
