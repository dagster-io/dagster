import re

import pytest

import dagster as dg
from dagster._core.errors import DagsterInvariantViolationError


def test_basic_build_input_context():
    context = dg.build_input_context()
    assert isinstance(context, dg.InputContext)


def test_build_input_context_with_resources():
    @dg.resource
    def foo_def():
        return "bar_def"

    context = dg.build_input_context(resources={"foo": "bar", "foo_def": foo_def})
    assert context.resources.foo == "bar"
    assert context.resources.foo_def == "bar_def"


def test_build_input_context_with_cm_resource():
    entered = []

    @dg.resource
    def cm_resource():
        try:
            yield "foo"
        finally:
            entered.append("yes")

    context = dg.build_input_context(resources={"cm_resource": cm_resource})
    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "At least one provided resource is a generator, but attempting to"
            " access resources outside of context manager scope. You can use the"
            " following syntax to open a context manager: `with"
            " build_input_context(...) as context:`",
        ),
    ):
        context.resources  # noqa: B018

    del context

    assert entered == ["yes"]

    with dg.build_input_context(resources={"cm_resource": cm_resource}) as context:
        assert context.resources.cm_resource == "foo"

    assert entered == ["yes", "yes"]


def test_basic_build_output_context():
    context = dg.build_output_context()
    assert isinstance(context, dg.OutputContext)


def test_build_output_context_with_cm_resource():
    entered = []

    @dg.resource
    def cm_resource():
        try:
            yield "foo"
        finally:
            entered.append("yes")

    context = dg.build_output_context(
        step_key="test", name="test", resources={"cm_resource": cm_resource}
    )
    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            "At least one provided resource is a generator, but attempting to"
            " access resources outside of context manager scope. You can use the"
            " following syntax to open a context manager: `with"
            " build_output_context(...) as context:`",
        ),
    ):
        context.resources  # noqa: B018

    del context

    assert entered == ["yes"]

    with dg.build_output_context(
        step_key="test", name="test", resources={"cm_resource": cm_resource}
    ) as context:
        assert context.resources.cm_resource == "foo"

    assert entered == ["yes", "yes"]


def test_context_logging_user_events():
    context = dg.build_output_context()

    context.log_event(dg.AssetMaterialization("first"))
    context.log_event(dg.AssetMaterialization("second"))
    assert [event.label for event in context.get_logged_events()] == ["first", "second"]


def test_context_logging_metadata():
    context = dg.build_output_context()

    context.add_output_metadata({"foo": "bar"})

    assert "foo" in context.get_logged_metadata()


def test_output_context_partition_key():
    context = dg.build_output_context(partition_key="foo")
    assert context.partition_key == "foo"
    assert context.has_partition_key


def test_input_context_partition_key():
    context = dg.build_input_context(partition_key="foo")
    assert context.partition_key == "foo"
    assert context.has_partition_key

    context = dg.build_input_context()
    assert not context.has_partition_key
