from dagster import graph

from consumption_datamart.phase_2.monitoring.report_active_customers_by_product_daily.it_should_conform_to_the_schema import it_should_conform_to_the_schema
from consumption_datamart.phase_2.monitoring.report_active_customers_by_product_daily.it_should_contain_current_data import it_should_contain_current_data


@graph
def validate_report_active_customers_by_product():
    """
    consumption_datamart.report_active_customers_by_product is one of the most important assets in the consumption datamart

    Each day it should contain a set of customers who are actively using each product based on usage data from the past 30 days

    The validate_report_active_customers_by_product graph validates that the asset contains expected data given various sets
    of input data in the lake.
    """

    it_should_conform_to_the_schema()
    it_should_contain_current_data()
