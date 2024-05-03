from dagster import AssetKey
from dagster_looker.asset_decorator import looker_assets

from .looker_projects import test_retail_demo_path


def test_asset_deps() -> None:
    @looker_assets(project_dir=test_retail_demo_path)
    def my_looker_assets(): ...

    assert my_looker_assets.asset_deps == {
        # Dashboards
        AssetKey(["dashboard", "address_deepdive"]): {
            AssetKey(["explore", "transactions"]),
        },
        AssetKey(["dashboard", "campaign_activation"]): {
            AssetKey(["explore", "omni_channel_transactions"])
        },
        AssetKey(["dashboard", "customer_360"]): {
            AssetKey(["explore", "omni_channel_transactions"])
        },
        AssetKey(["dashboard", "customer_deep_dive"]): {
            AssetKey(["explore", "customer_transaction_fact"])
        },
        AssetKey(["dashboard", "customer_segment_deepdive"]): {
            AssetKey(["explore", "transactions"])
        },
        AssetKey(["dashboard", "group_overview"]): {
            AssetKey(["explore", "transactions"]),
        },
        AssetKey(["dashboard", "item_affinity_analysis"]): {
            AssetKey(["explore", "order_purchase_affinity"])
        },
        AssetKey(["dashboard", "store_deepdive"]): {
            AssetKey(["explore", "transactions"]),
        },
        # Explores
        AssetKey(["explore", "customer_clustering_prediction"]): {
            AssetKey(["view", "customer_clustering_prediction"]),
            AssetKey(["view", "transactions"]),
        },
        AssetKey(["explore", "customer_event_fact"]): {AssetKey(["view", "customer_event_fact"])},
        AssetKey(["explore", "customer_transaction_fact"]): {
            AssetKey(["view", "customer_event_fact"]),
            AssetKey(["view", "customer_support_fact"]),
            AssetKey(["view", "customer_transaction_fact"]),
        },
        AssetKey(["explore", "omni_channel_events"]): {
            AssetKey(["view", "c360"]),
            AssetKey(["view", "omni_channel_events"]),
            AssetKey(["view", "omni_channel_transactions"]),
            AssetKey(["view", "omni_channel_transactions__transaction_details"]),
            AssetKey(["view", "retail_clv_predict"]),
        },
        AssetKey(["explore", "omni_channel_support_calls"]): {
            AssetKey(["view", "omni_channel_support_calls"]),
        },
        AssetKey(["explore", "omni_channel_transactions"]): {
            AssetKey(["view", "c360"]),
            AssetKey(["view", "customers"]),
            AssetKey(["view", "omni_channel_transactions"]),
            AssetKey(["view", "omni_channel_transactions__transaction_details"]),
            AssetKey(["view", "retail_clv_predict"]),
        },
        AssetKey(["explore", "order_purchase_affinity"]): {
            AssetKey(["view", "order_items_base"]),
            AssetKey(["view", "order_purchase_affinity"]),
            AssetKey(["view", "total_orders"]),
        },
        AssetKey(["explore", "stock_forecasting_explore_base"]): {
            AssetKey(["view", "stock_forecasting_explore_base"]),
            AssetKey(["view", "stock_forecasting_prediction"]),
        },
        AssetKey(["explore", "transactions"]): {
            AssetKey(["view", "channels"]),
            AssetKey(["view", "customer_clustering_prediction"]),
            AssetKey(["view", "customer_facts"]),
            AssetKey(["view", "customer_transaction_sequence"]),
            AssetKey(["view", "customers"]),
            AssetKey(["view", "products"]),
            AssetKey(["view", "store_weather"]),
            AssetKey(["view", "stores"]),
            AssetKey(["view", "transactions"]),
            AssetKey(["view", "transactions__line_items"]),
        },
    }
