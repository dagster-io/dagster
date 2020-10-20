import pytest
from dagster import DagsterInvalidConfigError, ModeDefinition, execute_pipeline, pipeline, solid
from docs_snippets.overview.configuration.config_map_example import unsigned_s3_session
from docs_snippets.overview.configuration.configured_example import east_unsigned_s3_session
from docs_snippets.overview.configuration.example import (
    run_bad_example,
    run_good_example,
    run_other_bad_example,
)


def test_config_example():
    assert run_good_example().success

    with pytest.raises(DagsterInvalidConfigError):
        run_bad_example()

    with pytest.raises(DagsterInvalidConfigError):
        run_other_bad_example()


def execute_pipeline_with_resource_def(resource_def, run_config=None):
    @solid(required_resource_keys={"key"})
    def a_solid(_):
        pass

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"key": resource_def})])
    def a_pipeline():
        a_solid()

    res = execute_pipeline(a_pipeline, run_config=run_config)
    assert res.success


def test_configured_example():
    execute_pipeline_with_resource_def(east_unsigned_s3_session)


def test_config_map_example():
    execute_pipeline_with_resource_def(
        unsigned_s3_session, run_config={"resources": {"key": {"config": {"region": "us-west-1"}}}}
    )
