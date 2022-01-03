import pytest

from consumption_datamart.repo import inmemory_consumption_datamart_job, inmemory_monitoring_job


@pytest.mark.usefixtures("daily_monitoring_job_results")
class Test_invoice_line_items:

    def test_daily_monitoring_should_succeed(self, daily_monitoring_job_results):
        assert daily_monitoring_job_results.success


@pytest.fixture(scope="class")
def daily_monitoring_job_results():
    # Execute the daily datamart creation job
    inmemory_consumption_datamart_job.execute_in_process()

    # Execute the monitoring job
    results = inmemory_monitoring_job.execute_in_process()

    return results
