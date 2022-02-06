import pytest

from consumption_datamart.phase_1.monitoring.report_active_customers_by_product_daily.validate_report_active_customers_by_product_graph import \
    validate_report_active_customers_by_product
from consumption_datamart.phase_1.repo import inmemory_consumption_datamart_job, inmemory_monitoring_job
from consumption_datamart_tests.common.job_assertions import assert_step_is_successful


@pytest.mark.parametrize("node_name", list(validate_report_active_customers_by_product.node_dict))
def test_validate_report_active_customers_by_product(monitoring_job_result, node_name):
    assert_step_is_successful('validate_report_active_customers_by_product', node_name, monitoring_job_result)


@pytest.fixture(scope="module")
def monitoring_job_result():
    # Execute the daily datamart creation job
    results = inmemory_consumption_datamart_job.execute_in_process(
        partition_key="2021-12-06"
    )
    assert results.success

    # Execute the monitoring job
    results = inmemory_monitoring_job.execute_in_process(
        partition_key="2021-12-06",
        raise_on_error=False
    )

    return results
