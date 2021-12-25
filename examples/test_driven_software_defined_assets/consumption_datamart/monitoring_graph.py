from dagster import graph

from consumption_datamart.assets.consumption_datamart.curated_views.active_customers_by_product_daily import \
    validate_active_customers_by_product_daily


@graph
def monitoring_daily():
    validate_active_customers_by_product_daily()
