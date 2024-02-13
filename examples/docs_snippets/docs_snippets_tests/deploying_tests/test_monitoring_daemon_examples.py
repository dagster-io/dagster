from docs_snippets.deploying.monitoring_daemon.run_timeouts import (
    MAX_RUNTIME_SECONDS_TAG,
    asset_job,
    my_job,
)


def test_run_timeouts():
    assert my_job.execute_in_process().success
    assert my_job.tags[MAX_RUNTIME_SECONDS_TAG] == "10"
    assert asset_job.tags[MAX_RUNTIME_SECONDS_TAG] == 10
