# ruff: noqa: UP006
import typing

import dagster as dg
import pytest
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_basic_python_dictionary_output():
    @dg.op(out=dg.Out(dict))
    def emit_dict():
        return {"key": "value"}

    assert wrap_op_in_graph_and_execute(emit_dict).output_value() == {"key": "value"}


def test_basic_python_dictionary_input():
    @dg.op(ins={"data": dg.In(dict)}, out=dg.Out(str))
    def input_dict(data):
        return data["key"]

    assert (
        wrap_op_in_graph_and_execute(
            input_dict, input_values={"data": {"key": "value"}}
        ).output_value()
        == "value"
    )


def test_basic_python_dictionary_wrong():
    @dg.op(out=dg.Out(dict))
    def emit_dict():
        return 1

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_dict)


def test_basic_python_dictionary_input_wrong():
    @dg.op(ins={"data": dg.In(dict)}, out=dg.Out(str))
    def input_dict(data):
        return data["key"]

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(input_dict, input_values={"data": 123})


def test_execute_dict_from_config():
    @dg.op(ins={"data": dg.In(dict)}, out=dg.Out(str))
    def input_dict(data):
        return data["key"]

    assert (
        wrap_op_in_graph_and_execute(
            input_dict,
            run_config={"ops": {"input_dict": {"inputs": {"data": {"key": "in_config"}}}}},
            do_input_mapping=False,
        ).output_value()
        == "in_config"
    )


def test_dagster_dictionary_output():
    @dg.op(out=dg.Out(dict))
    def emit_dict():
        return {"key": "value"}

    assert wrap_op_in_graph_and_execute(emit_dict).output_value() == {"key": "value"}


def test_basic_dagster_dictionary_input():
    @dg.op(ins={"data": dg.In(dg.Dict)}, out=dg.Out(str))  # pyright: ignore[reportArgumentType]
    def input_dict(data):
        return data["key"]

    assert (
        wrap_op_in_graph_and_execute(
            input_dict, input_values={"data": {"key": "value"}}
        ).output_value()
        == "value"
    )


def test_basic_typing_dictionary_output():
    @dg.op(out=dg.Out(typing.Dict))
    def emit_dict():
        return {"key": "value"}

    assert wrap_op_in_graph_and_execute(emit_dict).output_value() == {"key": "value"}


def test_basic_typing_dictionary_input():
    @dg.op(
        ins={"data": dg.In(typing.Dict)},
        out=dg.Out(str),
    )
    def input_dict(data):
        return data["key"]

    assert (
        wrap_op_in_graph_and_execute(
            input_dict, input_values={"data": {"key": "value"}}
        ).output_value()
        == "value"
    )


def test_basic_closed_typing_dictionary_wrong():
    @dg.op(out=dg.Out(typing.Dict[int, int]))
    def emit_dict():
        return 1

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_dict)


def test_basic_closed_typing_dictionary_output():
    @dg.op(out=dg.Out(typing.Dict[str, str]))
    def emit_dict():
        return {"key": "value"}

    assert wrap_op_in_graph_and_execute(emit_dict).output_value() == {"key": "value"}
    assert emit_dict.output_defs[0].dagster_type.key == "TypedPythonDict.String.String"
    assert emit_dict.output_defs[0].dagster_type.key_type.unique_name == "String"  # pyright: ignore[reportAttributeAccessIssue]
    assert emit_dict.output_defs[0].dagster_type.value_type.unique_name == "String"  # pyright: ignore[reportAttributeAccessIssue]


def test_basic_closed_typing_dictionary_input():
    @dg.op(
        ins={"data": dg.In(typing.Dict[str, str])},
        out=dg.Out(str),
    )
    def input_dict(data):
        return data["key"]

    assert (
        wrap_op_in_graph_and_execute(
            input_dict, input_values={"data": {"key": "value"}}
        ).output_value()
        == "value"
    )


def test_basic_closed_typing_dictionary_key_wrong():
    @dg.op(out=dg.Out(typing.Dict[str, str]))
    def emit_dict():
        return {1: "foo"}

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_dict)


def test_basic_closed_typing_dictionary_value_wrong():
    @dg.op(out=dg.Out(typing.Dict[str, str]))
    def emit_dict():
        return {"foo": 1}

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_dict)


def test_complicated_dictionary_typing_pass():
    @dg.op(out=dg.Out(typing.Dict[str, typing.List[typing.Dict[int, int]]]))
    def emit_dict():
        return {"foo": [{1: 1, 2: 2}]}

    assert wrap_op_in_graph_and_execute(emit_dict).output_value() == {"foo": [{1: 1, 2: 2}]}


def test_complicated_dictionary_typing_fail():
    @dg.op(out=dg.Out(typing.Dict[str, typing.List[typing.Dict[int, int]]]))
    def emit_dict():
        return {"foo": [{1: 1, "2": 2}]}

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        wrap_op_in_graph_and_execute(emit_dict)


def test_dict_type_loader():
    test_input = {"hello": 5, "goodbye": 42}

    @dg.op(ins={"dict_input": dg.In(dagster_type=typing.Dict[str, int])})
    def emit_dict(dict_input):
        return dict_input

    result = wrap_op_in_graph_and_execute(
        emit_dict,
        run_config={"ops": {"emit_dict": {"inputs": {"dict_input": test_input}}}},
        do_input_mapping=False,
    )
    assert result.success
    assert result.output_value() == test_input


def test_dict_type_loader_typing_fail():
    @dg.usable_as_dagster_type
    class CustomType(str):
        pass

    test_input = {"hello": "foo", "goodbye": "bar"}

    @dg.op(ins={"dict_input": dg.In(dagster_type=typing.Dict[str, CustomType])})
    def emit_dict(dict_input):
        return dict_input

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Input 'dict_input' of op 'emit_dict' has no way of being resolved.",
    ):
        wrap_op_in_graph_and_execute(
            emit_dict,
            run_config={"ops": {"emit_dict": {"inputs": {"dict_input": test_input}}}},
            do_input_mapping=False,
        )


def test_dict_type_loader_inner_type_mismatch():
    test_input = {"hello": "foo", "goodbye": "bar"}

    @dg.op(ins={"dict_input": dg.In(dagster_type=typing.Dict[str, int])})
    def emit_dict(dict_input):
        return dict_input

    with pytest.raises(dg.DagsterInvalidConfigError):
        wrap_op_in_graph_and_execute(
            emit_dict,
            run_config={"ops": {"emit_dict": {"inputs": {"dict_input": test_input}}}},
        )
