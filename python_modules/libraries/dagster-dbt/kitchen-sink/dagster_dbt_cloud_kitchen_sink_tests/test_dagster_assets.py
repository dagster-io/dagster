from dagster_dbt_cloud_kitchen_sink.defs import dbt_cloud_specs


def test_dbt_cloud_specs(ensure_cleanup: None) -> None:
    """Test that dbt Cloud asset specs are correctly loaded with the expected number of assets."""
    all_assets_keys = [asset.key for asset in dbt_cloud_specs]

    # 5 dbt models
    assert len(dbt_cloud_specs) == 5
    assert len(all_assets_keys) == 5

    # Sanity check outputs
    first_asset_key = next(key for key in sorted(all_assets_keys))
    assert first_asset_key.path == ["customer_metrics"]
