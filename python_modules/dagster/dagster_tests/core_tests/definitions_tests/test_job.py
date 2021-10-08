import pytest
from dagster import DagsterInvariantViolationError, job, op, resource


def get_job():
    @op(required_resource_keys={"foo"})
    def requires_foo(context):
        return context.resources.foo

    @resource
    def foo_resource():
        return "i am foo"

    @job(resource_defs={"foo": foo_resource})
    def my_job():
        requires_foo()

    return my_job


def test_with_resources():
    my_job = get_job()

    result = my_job.execute_in_process()
    assert result.success
    assert result.output_for_node("requires_foo") == "i am foo"

    @resource
    def injected_foo():
        return "i am injected foo"

    new_job = my_job.with_resources({"foo": injected_foo})
    result = new_job.execute_in_process()
    assert result.success
    assert result.output_for_node("requires_foo") == "i am injected foo"


def test_with_resources_value():
    my_job = get_job()

    new_job = my_job.with_resources({"foo": "i am injected foo"})
    result = new_job.execute_in_process()
    assert result.success
    assert result.output_for_node("requires_foo") == "i am injected foo"


def test_with_resources_nonexistent_key():
    my_job = get_job()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to remap resource 'bar' in job 'my_job', but no such resource exists on job.",
    ):
        my_job.with_resources({"bar": "blah"})
