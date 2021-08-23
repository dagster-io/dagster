import yaml
from dagster import ModeDefinition, execute_pipeline, pipeline, solid
from dagster.utils import file_relative_path
from docs_snippets_crag.concepts.configuration.config_map_example import unsigned_s3_session
from docs_snippets_crag.concepts.configuration.configured_example import (
    east_unsigned_s3_session,
    s3_session,
    west_signed_s3_session,
    west_unsigned_s3_session,
)


def test_config_map_example():
    execute_pipeline_with_resource_def(
        unsigned_s3_session, run_config={"resources": {"key": {"config": {"region": "us-east-1"}}}}
    )


def execute_pipeline_with_resource_def(resource_def, run_config=None):
    @solid(required_resource_keys={"key"})
    def a_solid():
        pass

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"key": resource_def})])
    def a_pipeline():
        a_solid()

    res = execute_pipeline(a_pipeline, run_config=run_config)
    assert res.success


def test_configured_example():
    execute_pipeline_with_resource_def(east_unsigned_s3_session)
    execute_pipeline_with_resource_def(west_unsigned_s3_session)
    execute_pipeline_with_resource_def(west_signed_s3_session)


def test_configured_example_yaml():
    with open(
        file_relative_path(
            __file__, "../../../docs_snippets_crag/concepts/configuration/configured_example.yaml"
        ),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())
    execute_pipeline_with_resource_def(s3_session, run_config)
