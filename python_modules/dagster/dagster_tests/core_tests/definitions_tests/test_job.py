import warnings

import pytest

from dagster import (
    DagsterInvariantViolationError,
    Field,
    StringSource,
    execute_pipeline,
    graph,
    job,
    op,
    reconstructable,
    static_partitioned_config,
)
from dagster.core.storage.tags import PARTITION_NAME_TAG
from dagster.core.test_utils import environ, instance_for_test


def define_the_job():
    @op
    def my_op():
        return 5

    @job
    def call_the_op():
        for _ in range(10):
            my_op()

    return call_the_op


def test_simple_job_no_warnings():

    # will fail if any warning is emitted
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        job = define_the_job()
        assert job.execute_in_process().success


def test_job_execution_multiprocess_config():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(define_the_job),
            instance=instance,
            run_config={"execution": {"config": {"multiprocess": {"max_concurrent": 4}}}},
        )

        assert result.success
        assert result.output_for_solid("my_op") == 5


results_lst = []


def define_in_process_job():
    @op
    def my_op():
        results_lst.append("entered")

    @job
    def call_the_op():
        for _ in range(10):
            my_op()

    return call_the_op


def test_switch_to_in_process_execution():
    result = execute_pipeline(
        define_in_process_job(),
        run_config={"execution": {"config": {"in_process": {}}}},
    )
    assert result.success
    assert len(results_lst) == 10


@graph
def basic_graph():
    pass


basic_job = basic_graph.to_job()  # type: ignore[union-attr]


def test_non_reconstructable_job_error():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="you must wrap the ``to_job`` call in a function at module scope",
    ):
        reconstructable(basic_job)


@job
def my_namespace_job():
    @op
    def inner_op():
        pass

    inner_op()


def test_reconstructable_job_namespace():
    with instance_for_test() as instance:
        result = execute_pipeline(reconstructable(my_namespace_job), instance=instance)

        assert result.success


def test_job_top_level_input():
    @job
    def my_job_with_input(x):
        @op
        def my_op(y):
            return y

        my_op(x)

    result = my_job_with_input.execute_in_process(run_config={"inputs": {"x": {"value": 2}}})
    assert result.success
    assert result.output_for_node("my_op") == 2


def test_job_post_process_config():
    @op(config_schema={"foo": Field(StringSource)})
    def the_op(context):
        return context.op_config["foo"]

    @graph
    def basic():
        the_op()

    with environ({"SOME_ENV_VAR": None}):
        # Ensure that the env var not existing will not throw an error, since resolution happens in post-processing.
        the_job = basic.to_job(
            config={"ops": {"the_op": {"config": {"foo": {"env": "SOME_ENV_VAR"}}}}}
        )

    with environ({"SOME_ENV_VAR": "blah"}):
        assert the_job.execute_in_process().success


def test_job_run_request():
    def partition_fn(partition_key: str):
        return {"ops": {"my_op": {"config": {"partition": partition_key}}}}

    @static_partitioned_config(partition_keys=["a", "b", "c", "d"])
    def my_partitioned_config(partition_key: str):
        return partition_fn(partition_key)

    @op
    def my_op():
        pass

    @job(config=my_partitioned_config)
    def my_job():
        my_op()

    for partition_key in ["a", "b", "c", "d"]:
        run_request = my_job.run_request_for_partition(partition_key=partition_key, run_key=None)
        assert run_request.run_config == partition_fn(partition_key)
        assert run_request.tags
        assert run_request.tags.get(PARTITION_NAME_TAG) == partition_key
