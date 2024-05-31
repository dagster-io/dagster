from dagster._core.definitions.asset_selection import AssetSelection


def test_asset_selection_with_config() -> None:
    bound_selection = AssetSelection.all().with_config({"config": "value"})
    assert bound_selection._ensure_unresolved_job().config == {"config": "value"}  # noqa
