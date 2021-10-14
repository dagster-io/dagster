import pytest
from dagster import pipeline, solid, validate_run_config
from dagster.core.errors import DagsterInvalidConfigError


def test_validate_run_config():
    @solid
    def basic():
        pass

    @pipeline
    def basic_pipeline():
        basic()

    validate_run_config(basic_pipeline)

    @solid(config_schema={"foo": str})
    def requires_config(_):
        pass

    @pipeline
    def pipeline_requires_config():
        requires_config()

    result = validate_run_config(
        pipeline_requires_config, {"solids": {"requires_config": {"config": {"foo": "bar"}}}}
    )

    assert result == {
        "solids": {"requires_config": {"config": {"foo": "bar"}, "inputs": {}, "outputs": None}},
        "execution": {"in_process": {"retries": {"enabled": {}}}},
        "resources": {"io_manager": {"config": None}},
        "loggers": {},
    }

    result_with_storage = validate_run_config(
        pipeline_requires_config,
        {"solids": {"requires_config": {"config": {"foo": "bar"}}}, "storage": {"filesystem": {}}},
    )

    assert result_with_storage == {
        "solids": {"requires_config": {"config": {"foo": "bar"}, "inputs": {}, "outputs": None}},
        "execution": {"in_process": {"retries": {"enabled": {}}}},
        "storage": {"filesystem": {}},
        "resources": {"io_manager": {"config": None}},
        "loggers": {},
    }

    with pytest.raises(DagsterInvalidConfigError):
        validate_run_config(pipeline_requires_config)
