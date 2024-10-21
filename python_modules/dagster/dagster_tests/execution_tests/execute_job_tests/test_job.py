import warnings
from datetime import datetime

import pytest
from dagster import (
    DagsterInvariantViolationError,
    Field,
    StringSource,
    execute_job,
    graph,
    job,
    op,
    reconstructable,
    static_partitioned_config,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.test_utils import environ, instance_for_test


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
        with execute_job(
            reconstructable(define_the_job),
            instance=instance,
            run_config={"execution": {"config": {"multiprocess": {"max_concurrent": 4}}}},
        ) as result:
            assert result.success
            assert result.output_for_node("my_op") == 5


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
    result = define_in_process_job().execute_in_process(
        run_config={"execution": {"config": {"in_process": {}}}},
    )
    assert result.success
    assert len(results_lst) == 10


@graph
def basic_graph():
    pass


basic_job = basic_graph.to_job()


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
        result = execute_job(reconstructable(my_namespace_job), instance=instance)
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

        run_request_with_tags = my_job.run_request_for_partition(
            partition_key=partition_key, run_key=None, tags={"foo": "bar"}
        )
        assert run_request_with_tags.run_config == partition_fn(partition_key)
        assert run_request_with_tags.tags
        assert run_request_with_tags.tags.get(PARTITION_NAME_TAG) == partition_key
        assert run_request_with_tags.tags.get("foo") == "bar"

    assert my_job.run_request_for_partition(partition_key="a", run_config={"a": 5}).run_config == {
        "a": 5
    }


# Datetime is not serializable
@op
def op_expects_date(the_date: datetime) -> str:
    return the_date.strftime("%m/%d/%Y")


@job(input_values={"the_date": datetime.now()})
def pass_from_job(the_date):
    op_expects_date(the_date)


def test_job_input_values_out_of_process():
    # Test job execution with non-serializable input type out-of-process

    assert pass_from_job.execute_in_process().success

    with instance_for_test() as instance:
        result = execute_job(reconstructable(pass_from_job), instance=instance)
        assert result.success


def test_subset_job_with_config():
    @op
    def echo(x: int):
        return x

    @job
    def no_config():
        echo(echo.alias("emit")())

    result = no_config.execute_in_process(run_config={"ops": {"emit": {"inputs": {"x": 1}}}})
    assert result.success

    subset_no_config = no_config.get_subset(op_selection=["echo"])

    result = subset_no_config.execute_in_process(run_config={"ops": {"echo": {"inputs": {"x": 1}}}})
    assert result.success

    @job(config={"ops": {"emit": {"inputs": {"x": 1}}}})
    def with_config():
        echo(echo.alias("emit")())

    result = with_config.execute_in_process()
    assert result.success

    subset_with_config = with_config.get_subset(op_selection=["echo"])

    result = subset_with_config.execute_in_process(
        run_config={"ops": {"echo": {"inputs": {"x": 1}}}}
    )
    assert result.success


def test_coerce_resource_job_decorator() -> None:
    executed = {}

    class BareResourceObject:
        pass

    @op(required_resource_keys={"bare_resource"})
    def an_op(context) -> None:
        assert context.resources.bare_resource
        executed["yes"] = True

    @job(resource_defs={"bare_resource": BareResourceObject()})
    def a_job() -> None:
        an_op()

    assert a_job.execute_in_process().success
    assert executed["yes"]


def test_coerce_resource_graph_to_job() -> None:
    executed = {}

    class BareResourceObject:
        pass

    @op(required_resource_keys={"bare_resource"})
    def an_op(context) -> None:
        assert context.resources.bare_resource
        executed["yes"] = True

    @graph
    def a_graph() -> None:
        an_op()

    a_job = a_graph.to_job(resource_defs={"bare_resource": BareResourceObject()})

    assert a_job.execute_in_process().success
    assert executed["yes"]


def test_job_tag_transfer():
    @op
    def my_op(): ...

    @graph
    def my_graph():
        my_op()

    my_job_tags_only = my_graph.to_job(tags={"foo": "bar"})
    assert my_job_tags_only.execute_in_process().dagster_run.tags == {"foo": "bar"}

    my_job_tags_and_empty_run_tags = my_graph.to_job(tags={"foo": "bar"}, run_tags={})
    assert my_job_tags_and_empty_run_tags.execute_in_process().dagster_run.tags == {}

    my_job_tags_and_nonempty_run_tags = my_graph.to_job(
        tags={"foo": "bar"}, run_tags={"baz": "quux"}
    )
    assert my_job_tags_and_nonempty_run_tags.execute_in_process().dagster_run.tags == {
        "baz": "quux"
    }
