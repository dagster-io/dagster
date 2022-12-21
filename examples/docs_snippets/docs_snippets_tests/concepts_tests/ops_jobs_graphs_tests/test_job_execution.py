import yaml

from dagster._legacy import execute_pipeline
from docs_snippets.concepts.ops_jobs_graphs.job_execution import (
    execute_subset,
    forkserver_job,
    ip_yaml,
    my_job,
)


def test_execute_my_job():
    result = my_job.execute_in_process()
    assert result.success


def test_solid_selection():
    execute_subset()


def test_yaml():
    execute_pipeline(my_job, run_config=yaml.safe_load(ip_yaml))


def test_forkserver():
    assert forkserver_job  # just assert definition created
