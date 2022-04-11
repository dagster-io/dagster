from dagster_pyspark.resources import pyspark_resource

from dagster import execute_pipeline, job, multiprocess_executor, op, reconstructable
from dagster.core.test_utils import instance_for_test


def assert_pipeline_runs_with_resource(resource_def):
    called = {}

    @op(required_resource_keys={"some_name"})
    def a_op():
        called["yup"] = True

    @job(resource_defs={"some_name": resource_def})
    def with_a_resource():
        a_op()

    result = with_a_resource.execute_in_process()

    assert result.success
    assert called["yup"]


def test_pyspark_resource():
    pyspark_resource.configured({"spark_conf": {"spark": {"executor": {"memory": "1024MB"}}}})
    assert_pipeline_runs_with_resource(pyspark_resource)


def test_pyspark_resource_escape_hatch():
    pyspark_resource.configured({"spark_conf": {"spark.executor.memory": "1024MB"}})
    assert_pipeline_runs_with_resource(pyspark_resource)


@op(required_resource_keys={"pyspark"})
def its_there(context):
    assert context.resources.pyspark


@job(
    resource_defs={"pyspark": pyspark_resource},
    executor_def=multiprocess_executor,
)
def multiproc_job():
    its_there()


def test_multiproc_preload():
    # Assert an multiprocess execution with a pyspark preload works.
    # This is in place due to pyspark.serializers._hijack_namedtuple causing issues with us if we
    # don't have defenses in place.

    with instance_for_test() as instance:

        # "smart" module preload
        result = execute_pipeline(reconstructable(multiproc_job), instance=instance)
        assert result.success

        # explicit module preload
        result = execute_pipeline(
            reconstructable(multiproc_job),
            run_config={
                "execution": {
                    "config": {"start_method": {"forkserver": {"preload_modules": ["pyspark"]}}}
                }
            },
            instance=instance,
        )
        assert result.success
