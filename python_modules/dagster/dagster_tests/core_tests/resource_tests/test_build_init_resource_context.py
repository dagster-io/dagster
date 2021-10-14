import pytest
from dagster import InitResourceContext, build_init_resource_context, resource
from dagster.core.errors import DagsterInvariantViolationError


def test_build_no_args():
    context = build_init_resource_context()
    assert isinstance(context, InitResourceContext)

    @resource
    def basic(_):
        return "foo"

    assert basic(context) == "foo"


def test_build_with_resources():
    @resource
    def foo(_):
        return "foo"

    context = build_init_resource_context(resources={"foo": foo, "bar": "bar"})
    assert context.resources.foo == "foo"
    assert context.resources.bar == "bar"

    @resource(required_resource_keys={"foo", "bar"})
    def reqs_resources(context):
        return context.resources.foo + context.resources.bar

    assert reqs_resources(context) == "foobar"


def test_build_with_cm_resource():
    entered = []

    @resource
    def foo(_):
        try:
            yield "foo"
        finally:
            entered.append("true")

    @resource(required_resource_keys={"foo"})
    def reqs_cm_resource(context):
        return context.resources.foo + "bar"

    context = build_init_resource_context(resources={"foo": foo})
    with pytest.raises(DagsterInvariantViolationError):
        context.resources  # pylint: disable=pointless-statement

    del context
    assert entered == ["true"]

    with build_init_resource_context(resources={"foo": foo}) as context:
        assert context.resources.foo == "foo"
        assert reqs_cm_resource(context) == "foobar"

    assert entered == ["true", "true"]
