import pytest

from consumption_datamart.repo import inmemory_consumption_datamart_job


@pytest.mark.usefixtures("dev_consumption_datamart")
class Test_consumption_datamart:

    def test_daily_monitoring_should_succeed(self, dev_consumption_datamart):
        assert dev_consumption_datamart.success


@pytest.fixture(scope="class")
def dev_consumption_datamart():
    results = inmemory_consumption_datamart_job.execute_in_process()

    return results
