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
        # Views
        AssetKey(["view", "c360"]): {
            AssetKey(["c360"]),
        },
        AssetKey(["view", "category_lookup"]): {
            AssetKey(["looker-private-demo", "retail", "category_lookup"])
        },
        AssetKey(["view", "channels"]): {
            AssetKey(["looker-private-demo", "retail", "channels"]),
        },
        AssetKey(["view", "customer_clustering_input"]): {
            AssetKey(["customer_clustering_input"]),
        },
        AssetKey(["view", "customer_clustering_model"]): {
            AssetKey(["customer_clustering_model"]),
        },
        AssetKey(["view", "customer_clustering_prediction"]): {
            AssetKey(["customer_clustering_prediction"])
        },
        AssetKey(["view", "customer_clustering_prediction_aggregates"]): {
            AssetKey(["customer_clustering_prediction_aggregates"])
        },
        AssetKey(["view", "customer_clustering_prediction_base"]): {
            AssetKey(["customer_clustering_prediction_base"])
        },
        AssetKey(["view", "customer_clustering_prediction_centroid_ranks"]): {
            AssetKey(["customer_clustering_prediction_centroid_ranks"])
        },
        AssetKey(["view", "customer_event_fact"]): {
            AssetKey(["customer_event_fact"]),
        },
        AssetKey(["view", "customer_facts"]): {
            AssetKey(["customer_facts"]),
        },
        AssetKey(["view", "customer_support_fact"]): {
            AssetKey(["customer_support_fact"]),
        },
        AssetKey(["view", "customer_transaction_fact"]): {
            AssetKey(["customer_transaction_fact"]),
        },
        AssetKey(["view", "customer_transaction_sequence"]): {
            AssetKey(["customer_transaction_sequence"]),
        },
        AssetKey(["view", "customers"]): {
            AssetKey(["looker-private-demo", "retail", "customers"]),
        },
        AssetKey(["view", "date_comparison"]): {
            AssetKey(["date_comparison"]),
        },
        AssetKey(["view", "distances"]): {
            AssetKey(["distances"]),
        },
        AssetKey(["view", "events"]): {
            AssetKey(["looker-private-demo", "retail", "events"]),
        },
        AssetKey(["view", "omni_channel_events"]): {
            AssetKey(["omni_channel_events"]),
        },
        AssetKey(["view", "omni_channel_support_calls"]): {
            AssetKey(["omni_channel_support_calls"])
        },
        AssetKey(["view", "omni_channel_support_calls__messages"]): {
            AssetKey(["omni_channel_support_calls__messages"])
        },
        AssetKey(["view", "omni_channel_transactions"]): {
            AssetKey(["omni_channel_transactions"]),
        },
        AssetKey(["view", "omni_channel_transactions__transaction_details"]): {
            AssetKey(["omni_channel_transactions__transaction_details"])
        },
        AssetKey(["view", "order_items"]): {
            AssetKey(["order_items"]),
        },
        AssetKey(["view", "order_items_base"]): {
            AssetKey(["order_items_base"]),
        },
        AssetKey(["view", "order_metrics"]): {
            AssetKey(["order_metrics"]),
        },
        AssetKey(["view", "order_product"]): {
            AssetKey(["order_product"]),
        },
        AssetKey(["view", "order_purchase_affinity"]): {
            AssetKey(["order_purchase_affinity"]),
        },
        AssetKey(["view", "orders"]): {
            AssetKey(["orders"]),
        },
        AssetKey(["view", "orders_by_product_loyal_users"]): {
            AssetKey(["orders_by_product_loyal_users"])
        },
        AssetKey(["view", "product_loyal_users"]): {
            AssetKey(["product_loyal_users"]),
        },
        AssetKey(["view", "products"]): {
            AssetKey(["looker-private-demo", "retail", "products"]),
        },
        AssetKey(["view", "retail_clv_predict"]): {
            AssetKey(["retail_ltv", "lpd_retail_clv_predict_tbl"])
        },
        AssetKey(["view", "stock_forecasting_category_week_facts_prior_year"]): {
            AssetKey(["stock_forecasting_category_week_facts_prior_year"])
        },
        AssetKey(["view", "stock_forecasting_explore_base"]): {
            AssetKey(["stock_forecasting_explore_base"])
        },
        AssetKey(["view", "stock_forecasting_input"]): {
            AssetKey(["stock_forecasting_input"]),
        },
        AssetKey(["view", "stock_forecasting_prediction"]): {
            AssetKey(["stock_forecasting_prediction"])
        },
        AssetKey(["view", "stock_forecasting_product_store_week_facts"]): {
            AssetKey(["stock_forecasting_product_store_week_facts"])
        },
        AssetKey(["view", "stock_forecasting_product_store_week_facts_prior_year"]): {
            AssetKey(["stock_forecasting_product_store_week_facts_prior_year"])
        },
        AssetKey(["view", "stock_forecasting_regression"]): {
            AssetKey(["stock_forecasting_regression"])
        },
        AssetKey(["view", "stock_forecasting_store_week_facts_prior_year"]): {
            AssetKey(["stock_forecasting_store_week_facts_prior_year"])
        },
        AssetKey(["view", "store_weather"]): {
            AssetKey(["store_weather"]),
        },
        AssetKey(["view", "stores"]): {
            AssetKey(["stores"]),
        },
        AssetKey(["view", "total_order_product"]): {
            AssetKey(["total_order_product"]),
        },
        AssetKey(["view", "total_orders"]): {
            AssetKey(["total_orders"]),
        },
        AssetKey(["view", "transaction_detail"]): {
            AssetKey(["transaction_detail"]),
        },
        AssetKey(["view", "transactions"]): {
            AssetKey(["looker-private-demo", "retail", "transaction_detail"])
        },
        AssetKey(["view", "transactions__line_items"]): {
            AssetKey(["transactions__line_items"]),
        },
        AssetKey(["view", "weather_pivoted"]): {
            AssetKey(["weather_pivoted"]),
        },
        AssetKey(["view", "weather_raw"]): {
            AssetKey(["weather_raw"]),
        },
    }
