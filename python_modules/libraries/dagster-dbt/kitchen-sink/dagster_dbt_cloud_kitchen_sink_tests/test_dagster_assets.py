from collections.abc import Sequence

import dagster as dg


def test_dbt_cloud_specs(dbt_cloud_specs: Sequence[dg.AssetSpec]) -> None:
    """Test that dbt Cloud asset specs are correctly loaded with the expected number of assets."""
    all_assets_keys = [asset.key for asset in dbt_cloud_specs]

    # 9 dbt models
    assert len(dbt_cloud_specs) == 9
    assert len(all_assets_keys) == 9

    # Sanity check outputs
    first_asset_key = next(key for key in sorted(all_assets_keys))
    assert first_asset_key.path == ["customer_metrics"]
