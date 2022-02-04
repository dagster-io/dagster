from dagster import graph

from consumption_datamart.monitoring.report_active_customers_by_product_daily.validate_report_active_customers_by_product_graph import \
    validate_report_active_customers_by_product


@graph()
def consumption_datamart_asset_validation_daily():
    validate_report_active_customers_by_product()
