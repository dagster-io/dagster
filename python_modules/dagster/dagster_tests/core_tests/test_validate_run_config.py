import dagster as dg
import pytest


def test_validate_run_config():
    @dg.op
    def basic():
        pass

    @dg.job
    def basic_job():
        basic()

    dg.validate_run_config(basic_job)

    @dg.op(config_schema={"foo": str})
    def requires_config(_):
        pass

    @dg.job
    def job_requires_config():
        requires_config()

    result = dg.validate_run_config(
        job_requires_config,
        {"ops": {"requires_config": {"config": {"foo": "bar"}}}},
    )

    assert result == {
        "ops": {"requires_config": {"config": {"foo": "bar"}, "inputs": {}, "outputs": None}},
        "execution": {
            "multi_or_in_process_executor": {
                "multiprocess": {
                    "max_concurrent": None,
                    "retries": {"enabled": {}},
                    "step_execution_mode": {"after_upstream_steps": {}},
                }
            }
        },
        "resources": {"io_manager": {"config": None}},
        "loggers": {},
    }

    with pytest.raises(dg.DagsterInvalidConfigError):
        dg.validate_run_config(job_requires_config)
