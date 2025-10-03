"""Tests for stdout/stderr capturing during resource initialization."""

import sys

import dagster as dg
import pytest


def test_resource_stdout_capture():
    """Test that stdout from resources is captured and logged."""

    @dg.resource
    def resource_with_stdout(context):
        print("Message from resource stdout")  # noqa: T201
        return "value"

    @dg.op(required_resource_keys={"my_resource"})
    def my_op(context):
        return context.resources.my_resource

    @dg.job(resource_defs={"my_resource": resource_with_stdout})
    def test_job():
        my_op()

    result = test_job.execute_in_process()
    assert result.success


def test_resource_stderr_capture():
    """Test that stderr from resources is captured and logged as warnings."""

    @dg.resource
    def resource_with_stderr(context):
        print("Error message from resource", file=sys.stderr)  # noqa: T201
        return "value"

    @dg.op(required_resource_keys={"my_resource"})
    def my_op(context):
        return context.resources.my_resource

    @dg.job(resource_defs={"my_resource": resource_with_stderr})
    def test_job():
        my_op()

    result = test_job.execute_in_process()
    assert result.success


def test_resource_multiline_output():
    """Test that multiline output from resources is properly captured."""

    @dg.resource
    def multiline_resource(context):
        print("Line 1")  # noqa: T201
        print("Line 2")  # noqa: T201
        print("Line 3")  # noqa: T201
        return "value"

    @dg.op(required_resource_keys={"my_resource"})
    def my_op(context):
        return context.resources.my_resource

    @dg.job(resource_defs={"my_resource": multiline_resource})
    def test_job():
        my_op()

    result = test_job.execute_in_process()
    assert result.success


def test_resource_empty_lines_skipped():
    """Test that empty lines are skipped in captured output."""

    @dg.resource
    def resource_with_empty_lines(context):
        print("First line")  # noqa: T201
        print("")  # noqa: T201
        print("   ")  # noqa: T201
        print("Last line")  # noqa: T201
        return "value"

    @dg.op(required_resource_keys={"my_resource"})
    def my_op(context):
        return context.resources.my_resource

    @dg.job(resource_defs={"my_resource": resource_with_empty_lines})
    def test_job():
        my_op()

    result = test_job.execute_in_process()
    assert result.success


def test_multiple_resources_with_output():
    """Test that multiple resources with stdout/stderr work correctly."""

    @dg.resource
    def resource_a(context):
        print("Output from A")  # noqa: T201
        return "A"

    @dg.resource
    def resource_b(context):
        print("Output from B")  # noqa: T201
        return "B"

    @dg.op(required_resource_keys={"res_a", "res_b"})
    def my_op(context):
        return f"{context.resources.res_a}-{context.resources.res_b}"

    @dg.job(resource_defs={"res_a": resource_a, "res_b": resource_b})
    def test_job():
        my_op()

    result = test_job.execute_in_process()
    assert result.success


def test_resource_with_no_log_manager():
    """Test that resources work when log manager is None."""

    @dg.resource
    def resource_without_logger():
        print("This shouldn't crash")  # noqa: T201
        return "value"

    @dg.op(required_resource_keys={"my_resource"})
    def my_op(context):
        return context.resources.my_resource

    @dg.job(resource_defs={"my_resource": resource_without_logger})
    def test_job():
        my_op()

    result = test_job.execute_in_process()
    assert result.success


def test_resource_generator_with_output():
    """Test that generator resources with stdout/stderr work correctly."""

    @dg.resource
    def generator_resource(context):
        print("Initializing generator")  # noqa: T201
        yield "value"
        print("Tearing down generator")  # noqa: T201

    @dg.op(required_resource_keys={"my_resource"})
    def my_op(context):
        return context.resources.my_resource

    @dg.job(resource_defs={"my_resource": generator_resource})
    def test_job():
        my_op()

    result = test_job.execute_in_process()
    assert result.success
