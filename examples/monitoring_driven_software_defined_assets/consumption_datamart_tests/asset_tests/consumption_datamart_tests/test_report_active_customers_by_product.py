import pytest

from consumption_datamart.monitoring.report_active_customers_by_product_daily import validate_report_active_customers_by_product
from consumption_datamart.repo import inmemory_consumption_datamart_job
from consumption_datamart.resources.datawarehouse_resources import inmemory_datawarehouse_resource
from consumption_datamart_tests.job_assertions import assert_step_is_successful, assert_step_is_failure


class Test_report_active_customers_by_product:
    """
    consumption_datamart.report_active_customers_by_product is one of the most important assets in the consumption datamart

    Each day it should contain a set of customers who are actively using each product based on usage data from the past 30 days

    The validate_report_active_customers_by_product graph validates that the asset contains expected data given various sets
    of input data in the lake.
    """

    @pytest.mark.parametrize("node_name", list(validate_report_active_customers_by_product.node_dict))
    def test_step_should_succeed_in_happy_path(self, happy_path_result, node_name):
        assert_step_is_successful(node_name, happy_path_result)

    @pytest.mark.skip("WIP - need to add test data that will cause a failure")
    def test_fail_when_missing_usage_facts(self, missing_usage_facts_result):
        assert_step_is_failure('it_should_contain_a_row_per_customer_product_combo', missing_usage_facts_result)


@pytest.fixture(scope="class")
def happy_path_result():
    # Execute the daily datamart creation job
    inmemory_consumption_datamart_job.execute_in_process()

    # Execute the monitoring job
    results = validate_report_active_customers_by_product.to_job(
        resource_defs={
            "datawarehouse": inmemory_datawarehouse_resource,
        }
    ).execute_in_process(raise_on_error=False)

    return results


@pytest.fixture(scope="class")
def missing_usage_facts_result():
    # TODO -setup some test data that will cause a failure

    # Execute the daily datamart creation job
    inmemory_consumption_datamart_job.execute_in_process()

    # Execute the monitoring job
    results = validate_report_active_customers_by_product.to_job(
        resource_defs={
            "datawarehouse": inmemory_datawarehouse_resource,
        }
    ).execute_in_process(raise_on_error=False)

    return results
