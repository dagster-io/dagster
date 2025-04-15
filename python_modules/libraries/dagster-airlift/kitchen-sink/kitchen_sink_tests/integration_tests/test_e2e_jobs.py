from dagster._core.instance_for_test import instance_for_test
from dagster_airlift.core.utils import monitoring_job_name
from dagster_airlift.test.test_utils import asset_spec
from kitchen_sink.airflow_instance import local_airflow_instance

from kitchen_sink_tests.integration_tests.conftest import (
    poll_for_airflow_run_existence_and_completion,
)


def test_job_based_defs(
    airflow_instance: None,
) -> None:
    """Test that job based defs load properly."""
    from kitchen_sink.dagster_defs.job_based_defs import defs

    assert len(defs.jobs) == 20  # type: ignore
    assert len(defs.assets) == 1  # type: ignore
    for key in ["print_asset", "another_print_asset", "example1", "example2"]:
        assert asset_spec(key, defs)

    # First, execute dataset producer dag
    af_instance = local_airflow_instance()
    af_run_id = af_instance.trigger_dag("dataset_producer")
    poll_for_airflow_run_existence_and_completion(
        af_instance=af_instance, af_run_id=af_run_id, dag_id="dataset_producer", duration=30
    )

    # Then, execute monitoring job
    with instance_for_test() as instance:
        result = defs.execute_job_in_process(
            monitoring_job_name(af_instance.name), instance=instance
        )
        assert result.success
        # There should be a run for the dataset producer dag and a run for the monitoring job
        runs = instance.get_runs()
        assert len(runs) == 2
