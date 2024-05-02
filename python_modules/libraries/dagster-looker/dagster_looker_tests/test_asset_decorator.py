from dagster import AssetKey
from dagster_looker.asset_decorator import looker_assets

from .looker_projects import test_retail_demo_path


def test_asset_deps() -> None:
    @looker_assets(project_dir=test_retail_demo_path)
    def my_looker_assets(): ...

    assert my_looker_assets.asset_deps == {
        AssetKey(["address_deepdive"]): {AssetKey(["transactions"])},
        AssetKey(["campaign_activation"]): {AssetKey(["omni_channel_transactions"])},
        AssetKey(["customer_360"]): {AssetKey(["omni_channel_transactions"])},
        AssetKey(["customer_deep_dive"]): {AssetKey(["customer_transaction_fact"])},
        AssetKey(["customer_segment_deepdive"]): {AssetKey(["transactions"])},
        AssetKey(["group_overview"]): {AssetKey(["transactions"])},
        AssetKey(["item_affinity_analysis"]): {AssetKey(["order_purchase_affinity"])},
        AssetKey(["store_deepdive"]): {AssetKey(["transactions"])},
    }
