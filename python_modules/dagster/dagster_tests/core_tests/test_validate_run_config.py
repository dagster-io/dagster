import pytest
from dagster import job, op, validate_run_config
from dagster._core.errors import DagsterInvalidConfigError


def test_validate_run_config():
    @op
    def basic():
        pass

    @job
    def basic_pipeline():
        basic()

    validate_run_config(basic_pipeline)

    @op(config_schema={"foo": str})
    def requires_config(_):
        pass

    @job
    def pipeline_requires_config():
        requires_config()

    result = validate_run_config(
        pipeline_requires_config, {"ops": {"requires_config": {"config": {"foo": "bar"}}}}
    )

    assert result == {
        "ops": {"requires_config": {"config": {"foo": "bar"}, "inputs": {}, "outputs": None}},
        "execution": {
            "multi_or_in_process_executor": {
                "multiprocess": {"max_concurrent": 0, "retries": {"enabled": {}}}
            }
        },
        "resources": {"io_manager": {"config": None}},
        "loggers": {},
    }

    with pytest.raises(DagsterInvalidConfigError):
        validate_run_config(pipeline_requires_config)
