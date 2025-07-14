import dagster as dg
import pytest


def test_string_from_inputs():
    called = {}

    @dg.op(ins={"string_input": dg.In(dg.String)})
    def str_as_input(_context, string_input):
        assert string_input == "foo"
        called["yup"] = True

    foo_job = dg.JobDefinition(
        graph_def=dg.GraphDefinition(name="test_string_from_inputs_job", node_defs=[str_as_input])
    )

    result = foo_job.execute_in_process(
        run_config={"ops": {"str_as_input": {"inputs": {"string_input": {"value": "foo"}}}}},
    )

    assert result.success
    assert called["yup"]


def test_string_from_aliased_inputs():
    called = {}

    @dg.op(ins={"string_input": dg.In(dg.String)})
    def str_as_input(_context, string_input):
        assert string_input == "foo"
        called["yup"] = True

    foo_job = dg.JobDefinition(
        graph_def=dg.GraphDefinition(
            node_defs=[str_as_input],
            name="test",
            dependencies={dg.NodeInvocation("str_as_input", alias="aliased"): {}},
        )
    )

    result = foo_job.execute_in_process(
        run_config={"ops": {"aliased": {"inputs": {"string_input": {"value": "foo"}}}}},
    )

    assert result.success
    assert called["yup"]


def test_string_missing_inputs():
    called = {}

    @dg.op(ins={"string_input": dg.In(dg.String)})
    def str_as_input(_context, string_input):
        called["yup"] = True

    foo_job = dg.JobDefinition(
        graph_def=dg.GraphDefinition(name="missing_inputs", node_defs=[str_as_input])
    )
    with pytest.raises(dg.DagsterInvalidConfigError) as exc_info:
        foo_job.execute_in_process()

    assert len(exc_info.value.errors) == 1

    expected_suggested_config = {"ops": {"str_as_input": {"inputs": {"string_input": "..."}}}}
    assert exc_info.value.errors[0].message.startswith(
        'Missing required config entry "ops" at the root.'
    )
    assert str(expected_suggested_config) in exc_info.value.errors[0].message

    assert "yup" not in called


def test_string_missing_input_collision():
    called = {}

    @dg.op(out=dg.Out(dg.String))
    def str_as_output(_context):
        return "bar"

    @dg.op(ins={"string_input": dg.In(dg.String)})
    def str_as_input(_context, string_input):
        called["yup"] = True

    foo_job = dg.JobDefinition(
        graph_def=dg.GraphDefinition(
            name="overlapping",
            node_defs=[str_as_input, str_as_output],
            dependencies={
                "str_as_input": {"string_input": dg.DependencyDefinition("str_as_output")}
            },
        )
    )
    with pytest.raises(dg.DagsterInvalidConfigError) as exc_info:
        foo_job.execute_in_process(
            run_config={"ops": {"str_as_input": {"inputs": {"string_input": "bar"}}}}
        )

    assert (
        'Error 1: Received unexpected config entry "inputs" at path root:ops:str_as_input.'
        in str(exc_info.value)
    )

    assert "yup" not in called


def test_composite_input_type():
    called = {}

    @dg.op(ins={"list_string_input": dg.In(dg.List[dg.String])})
    def str_as_input(_context, list_string_input):
        assert list_string_input == ["foo"]
        called["yup"] = True

    foo_job = dg.JobDefinition(
        graph_def=dg.GraphDefinition(name="test_string_from_inputs_job", node_defs=[str_as_input])
    )

    result = foo_job.execute_in_process(
        run_config={"ops": {"str_as_input": {"inputs": {"list_string_input": [{"value": "foo"}]}}}},
    )

    assert result.success
    assert called["yup"]
