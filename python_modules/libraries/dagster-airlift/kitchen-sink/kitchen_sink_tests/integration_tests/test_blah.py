import os
import sys

from dagster_airlift.test.shared_fixtures import stand_up_airflow

from kitchen_sink_tests.integration_tests.conftest import makefile_dir


def test_af_instance(local_env: None, expected_num_dags: int):
    with stand_up_airflow(
        airflow_cmd=["make", "run_airflow"],
        env=os.environ,
        cwd=makefile_dir(),
        expected_num_dags=expected_num_dags,
        # Send stdout to the console
        stdout_channel=sys.stdout,
    ) as process:
        print("AIRFLOW IS STOOD UP")
        print("-------------")
