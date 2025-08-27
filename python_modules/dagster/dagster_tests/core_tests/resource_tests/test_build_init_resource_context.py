import dagster as dg
import pytest


def test_build_no_args():
    context = dg.build_init_resource_context()
    assert isinstance(context, dg.InitResourceContext)

    @dg.resource
    def basic(_):
        return "foo"

    assert basic(context) == "foo"


def test_build_with_resources():
    @dg.resource
    def foo(_):
        return "foo"

    context = dg.build_init_resource_context(resources={"foo": foo, "bar": "bar"})
    assert context.resources.foo == "foo"
    assert context.resources.bar == "bar"

    @dg.resource(required_resource_keys={"foo", "bar"})
    def reqs_resources(context):
        return context.resources.foo + context.resources.bar

    assert reqs_resources(context) == "foobar"


def test_build_with_cm_resource():
    entered = []

    @dg.resource
    def foo(_):
        try:
            yield "foo"
        finally:
            entered.append("true")

    @dg.resource(required_resource_keys={"foo"})
    def reqs_cm_resource(context):
        return context.resources.foo + "bar"

    context = dg.build_init_resource_context(resources={"foo": foo})
    with pytest.raises(dg.DagsterInvariantViolationError):
        context.resources  # noqa: B018

    del context
    assert entered == ["true"]

    with dg.build_init_resource_context(resources={"foo": foo}) as context:  # pyright: ignore[reportGeneralTypeIssues]
        assert context.resources.foo == "foo"
        assert reqs_cm_resource(context) == "foobar"

    assert entered == ["true", "true"]
