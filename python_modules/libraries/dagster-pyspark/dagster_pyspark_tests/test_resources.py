from typing import Any

import pytest
from dagster import job, multiprocess_executor, op, reconstructable
from dagster._core.execution.api import execute_job
from dagster._core.test_utils import instance_for_test
from dagster_pyspark import (
    LazyPySparkResource,
    PySparkResource,
    lazy_pyspark_resource,
    pyspark_resource,
)
from pyspark.sql import SparkSession


def assert_job_runs_with_resource(resource_def):
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


def assert_job_runs_with_lazy_resource(resource_def):
    called = {}

    @op(required_resource_keys={"some_name"})
    def a_op(context):
        assert context.resources.some_name._spark_session is None  # noqa: SLF001
        assert isinstance(context.resources.some_name.spark_session, SparkSession)
        assert isinstance(
            context.resources.some_name._spark_session,  # noqa: SLF001
            SparkSession,
        )
        called["yup"] = True

    @job(resource_defs={"some_name": resource_def})
    def with_a_resource():
        a_op()

    result = with_a_resource.execute_in_process()

    assert result.success
    assert called["yup"]


@pytest.fixture(name="build_pyspark_resource", params=["pythonic", "legacy"])
def build_pyspark_resource_fixture(request) -> Any:
    if request.param == "pythonic":
        return PySparkResource
    else:
        return lambda **kwargs: pyspark_resource.configured(
            {"spark_conf": kwargs.get("spark_config")}
        )


@pytest.fixture(name="build_lazy_pyspark_resource", params=["pythonic", "legacy"])
def build_lazy_pyspark_resource_fixture(request) -> Any:
    if request.param == "pythonic":
        return LazyPySparkResource
    else:
        return lambda **kwargs: lazy_pyspark_resource.configured(
            {"spark_conf": kwargs.get("spark_config")}
        )


def test_pyspark_resource(build_pyspark_resource):
    build_pyspark_resource(spark_config={"spark": {"executor": {"memory": "1024MB"}}})
    assert_job_runs_with_resource(pyspark_resource)


def test_lazy_pyspark_resource(build_lazy_pyspark_resource):
    build_lazy_pyspark_resource(spark_config={"spark": {"executor": {"memory": "1024MB"}}})
    assert_job_runs_with_lazy_resource(lazy_pyspark_resource)


def test_pyspark_resource_escape_hatch(build_pyspark_resource):
    build_pyspark_resource(spark_config={"spark.executor.memory": "1024MB"})
    assert_job_runs_with_resource(pyspark_resource)


def test_lazy_pyspark_resource_escape_hatch(build_lazy_pyspark_resource):
    build_lazy_pyspark_resource(spark_config={"spark.executor.memory": "1024MB"})
    assert_job_runs_with_lazy_resource(lazy_pyspark_resource)


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
        with execute_job(reconstructable(multiproc_job), instance=instance) as result:
            assert result.success

        # explicit module preload
        with execute_job(
            reconstructable(multiproc_job),
            run_config={
                "execution": {
                    "config": {"start_method": {"forkserver": {"preload_modules": ["pyspark"]}}}
                }
            },
            instance=instance,
        ) as result:
            assert result.success
