import os

import pytest
from dagster_airlift.test.test_utils import get_job_from_defs


@pytest.mark.skipif(
    os.getenv("BUILDKITE") is not None,
    reason="Skipping MWAA tests on Buildkite. We need to add creds to buildkite which can access the MWAA environment.",
)
def test_mwaa_backend():
    from dagster_airlift_tests.mwaa_integration_tests.dagster_defs.defs import defs_obj

    assert defs_obj.jobs
    assert len(list(defs_obj.jobs)) > 1
    assert get_job_from_defs("dag_0", defs_obj)
    assert get_job_from_defs("my_airflow_instance__airflow_monitoring_job", defs_obj)
