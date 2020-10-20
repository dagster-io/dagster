from dagster import ModeDefinition, PipelineDefinition, execute_pipeline, solid
from dagster_pyspark.resources import pyspark_resource


def assert_pipeline_runs_with_resource(resource_def):
    called = {}

    @solid(required_resource_keys={"some_name"})
    def a_solid(_):
        called["yup"] = True

    pipeline_def = PipelineDefinition(
        name="with_a_resource",
        solid_defs=[a_solid],
        mode_defs=[ModeDefinition(resource_defs={"some_name": resource_def})],
    )

    result = execute_pipeline(pipeline_def)

    assert result.success
    assert called["yup"]


def test_pyspark_resource():
    pyspark_resource.configured({"spark_conf": {"spark": {"executor": {"memory": "1024MB"}}}})
    assert_pipeline_runs_with_resource(pyspark_resource)


def test_pyspark_resource_escape_hatch():
    pyspark_resource.configured({"spark_conf": {"spark.executor.memory": "1024MB"}})
    assert_pipeline_runs_with_resource(pyspark_resource)
