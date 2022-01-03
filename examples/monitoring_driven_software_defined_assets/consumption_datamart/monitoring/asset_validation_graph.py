from consumption_datamart.monitoring.report_active_customers_by_product_daily import validate_report_active_customers_by_product
from dagster import graph


@graph()
def consumption_datamart_asset_validation_daily():
    validate_report_active_customers_by_product()
