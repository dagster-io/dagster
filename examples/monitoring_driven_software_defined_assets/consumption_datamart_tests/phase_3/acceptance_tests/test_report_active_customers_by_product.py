import pytest

from consumption_datamart.phase_3.monitoring.report_active_customers_by_product_daily import \
    validate_report_active_customers_by_product
from consumption_datamart.phase_3.repo import inmemory_consumption_datamart_job
from consumption_datamart.common.resources import inmemory_datawarehouse_resource
from consumption_datamart_tests.common.job_assertions import assert_step_is_successful


class Test_report_active_customers_by_product:

    @pytest.mark.parametrize("node_name", list(validate_report_active_customers_by_product.node_dict))
    def test_validate_report_active_customers_by_product_checks_should_succeed_in_happy_path(self, happy_path_result, node_name):
        assert_step_is_successful(node_name, happy_path_result)


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
