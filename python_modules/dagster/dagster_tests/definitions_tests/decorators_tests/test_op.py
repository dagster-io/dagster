import re
import time
from functools import partial
from typing import Any, Dict, Generator, List, Tuple

import pytest
from dagster import (
    AssetMaterialization,
    AssetObservation,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DagsterType,
    DagsterTypeCheckDidNotPass,
    DynamicOut,
    DynamicOutput,
    ExpectationResult,
    In,
    Nothing,
    Out,
    Output,
    build_op_context,
    graph,
    job,
    mem_io_manager,
    op,
)
from dagster._config.field import Field
from dagster._core.definitions.dependency import DependencyDefinition
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.test_utils import instance_for_test
from dagster._core.types.dagster_type import Int, String
from dagster._core.utility_ops import create_stub_op


def execute_in_graph(an_op, raise_on_error=True, run_config=None):
    @graph
    def my_graph():
        an_op()

    result = my_graph.execute_in_process(raise_on_error=raise_on_error, run_config=run_config)
    return result


def test_no_parens_op():
    called = {}

    @op
    def hello_world():
        called["yup"] = True

    execute_in_graph(hello_world)

    assert called["yup"]


def test_empty_op():
    called = {}

    @op()
    def hello_world():
        called["yup"] = True

    execute_in_graph(hello_world)

    assert called["yup"]


def test_op():
    @op(out=Out())
    def hello_world(_context):
        return {"foo": "bar"}

    result = execute_in_graph(hello_world)

    assert result.success
    assert result.output_for_node("hello_world")["foo"] == "bar"


def test_op_one_output():
    @op
    def hello_world():
        return {"foo": "bar"}

    result = execute_in_graph(hello_world)

    assert result.success
    assert result.output_for_node("hello_world")["foo"] == "bar"


def test_op_yield():
    @op(out=Out())
    def hello_world(_context):
        yield Output(value={"foo": "bar"})

    result = execute_in_graph(hello_world)

    assert result.success
    assert result.output_for_node("hello_world")["foo"] == "bar"


def test_op_result_return():
    @op(out=Out())
    def hello_world(_context):
        return Output(value={"foo": "bar"})

    result = execute_in_graph(hello_world)

    assert result.success
    assert result.output_for_node("hello_world")["foo"] == "bar"


def test_op_with_explicit_empty_outputs():
    @op(out={})
    def hello_world(_context):
        return "foo"

    with pytest.raises(DagsterInvariantViolationError):
        execute_in_graph(hello_world)


def test_op_with_implicit_single_output():
    @op()
    def hello_world(_context):
        return "foo"

    result = execute_in_graph(hello_world)

    assert result.success
    assert result.output_for_node("hello_world") == "foo"


def test_op_return_list_instead_of_multiple_results():
    @op(out={"foo": Out(), "bar": Out()})
    def hello_world(_context):
        return ["foo", "bar"]

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        execute_in_graph(hello_world)


def test_op_with_name():
    @op(name="foobar", out=Out())
    def hello_world(_context):
        return {"foo": "bar"}

    result = execute_in_graph(hello_world)

    assert result.success
    assert result.output_for_node("foobar")["foo"] == "bar"


def test_op_with_input():
    @op(ins={"foo_to_foo": In()})
    def hello_world(foo_to_foo):
        return foo_to_foo

    the_job = JobDefinition(
        graph_def=GraphDefinition(
            node_defs=[create_stub_op("test_value", {"foo": "bar"}), hello_world],
            name="test",
            dependencies={"hello_world": {"foo_to_foo": DependencyDefinition("test_value")}},
        )
    )

    result = the_job.execute_in_process()

    assert result.success
    assert result.output_for_node("hello_world") == {"foo": "bar"}


def test_op_definition_errors():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape("positional vararg parameter '*args'"),
    ):

        @op(ins={"foo": In()}, out=Out())
        def vargs(context, foo, *args):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @op(ins={"foo": In()}, out=Out())
        def wrong_name(context, bar):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @op(
            ins={"foo": In(), "bar": In()},
            out=Out(),
        )
        def wrong_name_2(context, foo):
            pass

    @op(
        ins={"foo": In(), "bar": In()},
        out=Out(),
    )
    def valid_kwargs(context, **kwargs):
        pass

    @op(
        ins={"foo": In(), "bar": In()},
        out=Out(),
    )
    def valid(context, foo, bar):
        pass

    @op
    def valid_because_inference(context, foo, bar):
        pass


def test_wrong_argument_to_job():
    def non_solid_func():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="You have passed a lambda or function non_solid_func",
    ):
        GraphDefinition(node_defs=[non_solid_func], name="test")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="You have passed a lambda or function <lambda>",
    ):
        GraphDefinition(node_defs=[lambda x: x], name="test")


def test_descriptions():
    @op(description="foo")
    def op_desc(_context):
        pass

    assert op_desc.description == "foo"


def test_any_config_field():
    called = {}
    conf_value = 234

    @op(config_schema=Field(Any))
    def hello_world(context):
        assert context.op_config == conf_value
        called["yup"] = True

    execute_in_graph(hello_world, run_config={"ops": {"hello_world": {"config": conf_value}}})

    assert called["yup"]


def test_op_required_resources_no_arg():
    @op(required_resource_keys={"foo"})
    def _noop():
        return


def test_op_config_no_arg():
    @op(config_schema={"foo": str})
    def _noop2():
        return


def test_op_docstring():
    @op
    def foo_op(_):
        """FOO_DOCSTRING."""
        return

    @op
    def bar_op():
        """BAR_DOCSTRING."""
        return

    @op(name="baz")
    def baz_op(_):
        """BAZ_DOCSTRING."""
        return

    @op(name="quux")
    def quux_op():
        """QUUX_DOCSTRING."""
        return

    @graph
    def comp_graph():
        """COMP_DOCSTRING."""
        foo_op()

    @job
    def the_job():
        """THE_DOCSTRING."""
        quux_op()

    @op
    def the_op():
        """OP_DOCSTRING."""

    @graph
    def the_graph():
        """GRAPH_DOCSTRING."""
        the_op()

    assert foo_op.__doc__ == "FOO_DOCSTRING."
    assert foo_op.description == "FOO_DOCSTRING."
    assert foo_op.__name__ == "foo_op"
    assert bar_op.__doc__ == "BAR_DOCSTRING."
    assert bar_op.description == "BAR_DOCSTRING."
    assert bar_op.__name__ == "bar_op"
    assert baz_op.__doc__ == "BAZ_DOCSTRING."
    assert baz_op.description == "BAZ_DOCSTRING."
    assert baz_op.__name__ == "baz_op"
    assert quux_op.__doc__ == "QUUX_DOCSTRING."
    assert quux_op.description == "QUUX_DOCSTRING."
    assert quux_op.__name__ == "quux_op"
    assert comp_graph.__doc__ == "COMP_DOCSTRING."
    assert comp_graph.description == "COMP_DOCSTRING."
    assert comp_graph.__name__ == "comp_graph"
    assert the_job.__doc__ == "THE_DOCSTRING."
    assert the_job.description == "THE_DOCSTRING."
    assert the_job.__name__ == "the_job"
    assert the_op.__doc__ == "OP_DOCSTRING."
    assert the_op.description == "OP_DOCSTRING."
    assert the_op.__name__ == "the_op"
    assert the_graph.__doc__ == "GRAPH_DOCSTRING."
    assert the_graph.description == "GRAPH_DOCSTRING."
    assert the_graph.__name__ == "the_graph"


def test_op_yields_single_bare_value():
    @op
    def return_iterator(_):
        yield 1

    with pytest.raises(
        DagsterInvariantViolationError,
        match="yielded a value of type <class 'int'>",
    ):
        execute_in_graph(return_iterator)


def test_op_yields_multiple_bare_values():
    @op
    def return_iterator(_):
        yield 1
        yield 2

    with pytest.raises(
        DagsterInvariantViolationError,
        match="yielded a value of type <class 'int'>",
    ):
        execute_in_graph(return_iterator)


def test_op_returns_iterator():
    def iterator():
        for i in range(3):
            yield i

    @op
    def return_iterator(_):
        return iterator()

    with pytest.raises(
        DagsterInvariantViolationError, match="yielded a value of type <class 'int'>"
    ):
        execute_in_graph(return_iterator)


def test_input_default():
    @op
    def foo(bar="ok"):
        return bar

    result = execute_in_graph(foo)
    assert result.output_for_node("foo") == "ok"


def execute_op_in_graph(an_op, instance=None, resources=None):
    @graph
    def my_graph():
        an_op()

    result = my_graph.execute_in_process(instance=instance, resources=resources)
    return result


def test_no_outs():
    @op(out={})
    def the_op():
        pass

    assert len(the_op.output_defs) == 0
    result = execute_op_in_graph(the_op)
    assert result.success

    @op(out={})
    def the_out_op():
        pass

    assert len(the_op.outs) == 0


def test_ins():
    @op
    def upstream1():
        return 5

    @op
    def upstream2():
        return "6"

    @op(ins={"a": In(metadata={"x": 1}), "b": In(metadata={"y": 2})})
    def my_op(a: int, b: str) -> int:
        return a + int(b)

    assert my_op.ins == {
        "a": In(metadata={"x": 1}, dagster_type=Int),
        "b": In(metadata={"y": 2}, dagster_type=String),
    }

    @graph
    def my_graph():
        my_op(a=upstream1(), b=upstream2())

    result = my_graph.execute_in_process()
    assert result.success

    assert upstream1() == 5

    assert upstream2() == "6"

    assert my_op(1, "2") == 3


def test_ins_dagster_types():
    assert In(dagster_type=None)
    assert In(dagster_type=int)
    assert In(dagster_type=List)
    assert In(dagster_type=List[int])  # typing type
    assert In(dagster_type=Int)  # dagster type


def test_out():
    @op(out=Out(metadata={"x": 1}))
    def my_op() -> int:
        """
        Returns:
            int: some int
        """  # noqa: D212, D415
        return 1

    assert my_op.outs == {
        "result": Out(
            metadata={"x": 1},
            dagster_type=Int,
            is_required=True,
            io_manager_key="io_manager",
            description="some int",
        )
    }
    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "result"
    assert my_op() == 1


def test_out_dagster_types():
    assert Out(dagster_type=None)
    assert Out(dagster_type=int)
    assert Out(dagster_type=List)
    assert Out(dagster_type=List[int])  # typing type
    assert Out(dagster_type=Int)  # dagster type


def test_multi_out():
    @op(
        out={
            "a": Out(metadata={"x": 1}, code_version="foo"),
            "b": Out(metadata={"y": 2}, code_version="bar"),
        }
    )
    def my_op() -> Tuple[int, str]:
        return 1, "q"

    assert len(my_op.output_defs) == 2
    assert all([output_def.description is None for output_def in my_op.output_defs])

    assert my_op.outs == {
        "a": Out(
            metadata={"x": 1},
            dagster_type=Int,
            is_required=True,
            io_manager_key="io_manager",
            code_version="foo",
        ),
        "b": Out(
            metadata={"y": 2},
            dagster_type=String,
            is_required=True,
            io_manager_key="io_manager",
            code_version="bar",
        ),
    }
    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[0].code_version == "foo"
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"
    assert my_op.output_defs[1].code_version == "bar"

    assert my_op() == (1, "q")


def test_tuple_out():
    @op
    def my_op() -> Tuple[int, str]:
        return 1, "a"

    assert len(my_op.output_defs) == 1
    result = execute_op_in_graph(my_op)
    assert result.output_for_node("my_op") == (1, "a")

    assert my_op() == (1, "a")


def test_multi_out_yields():
    @op(out={"a": Out(metadata={"x": 1}), "b": Out(metadata={"y": 2})})
    def my_op():
        yield Output(output_name="a", value=1)
        yield Output(output_name="b", value=2)

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"
    result = execute_op_in_graph(my_op)
    assert result.output_for_node("my_op", "a") == 1
    assert result.output_for_node("my_op", "b") == 2

    assert [output.value for output in my_op()] == [1, 2]


def test_multi_out_optional():
    @op(
        out={
            "a": Out(metadata={"x": 1}, is_required=False),
            "b": Out(metadata={"y": 2}),
        }
    )
    def my_op():
        yield Output(output_name="b", value=2)

    result = execute_op_in_graph(my_op)
    assert result.output_for_node("my_op", "b") == 2

    assert [output.value for output in my_op()] == [2]


def test_ins_dict():
    @op
    def upstream1():
        return 5

    @op
    def upstream2():
        return "6"

    @op(
        ins={
            "a": In(metadata={"x": 1}),
            "b": In(metadata={"y": 2}),
        }
    )
    def my_op(a: int, b: str) -> int:
        return a + int(b)

    assert my_op.input_defs[0].dagster_type.typing_type == int
    assert my_op.input_defs[1].dagster_type.typing_type == str

    @graph
    def my_graph():
        my_op(a=upstream1(), b=upstream2())

    result = my_graph.execute_in_process()
    assert result.success

    assert my_op(a=1, b="2") == 3


def test_multi_out_dict():
    @op(out={"a": Out(metadata={"x": 1}), "b": Out(metadata={"y": 2})})
    def my_op() -> Tuple[int, str]:
        return 1, "q"

    assert len(my_op.output_defs) == 2

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[0].dagster_type.typing_type == int
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"
    assert my_op.output_defs[1].dagster_type.typing_type == str

    result = execute_op_in_graph(my_op)
    assert result.output_for_node("my_op", "a") == 1
    assert result.output_for_node("my_op", "b") == "q"

    assert my_op() == (1, "q")


def test_nothing_in():
    @op(out=Out(dagster_type=Nothing))
    def noop():
        pass

    @op(ins={"after": In(dagster_type=Nothing)})
    def on_complete():
        return "cool"

    @graph
    def nothing_test():
        on_complete(noop())

    result = nothing_test.execute_in_process()
    assert result.success


def test_op_config():
    @op(config_schema={"conf_str": str})
    def my_op(context):
        assert context.op_config == {"conf_str": "foo"}

    my_op(build_op_context(config={"conf_str": "foo"}))

    @graph
    def basic():
        my_op()

    result = basic.execute_in_process(
        run_config={"ops": {"my_op": {"config": {"conf_str": "foo"}}}}
    )

    assert result.success

    result = basic.to_job(
        config={"ops": {"my_op": {"config": {"conf_str": "foo"}}}}
    ).execute_in_process()
    assert result.success


even_type = DagsterType(
    name="EvenDagsterType",
    type_check_fn=lambda _, value: isinstance(value, int) and value % 2 == 0,
)


# Test typing override between out and annotation. Should they just match?
def test_out_dagster_type():
    @op(out=Out(dagster_type=even_type))
    def basic() -> int:
        return 6

    assert basic.output_defs[0].dagster_type == even_type
    assert basic() == 6


def test_multiout_dagster_type():
    @op(out={"a": Out(dagster_type=even_type), "b": Out(dagster_type=even_type)})
    def basic_multi() -> Tuple[int, int]:
        return 6, 6

    assert basic_multi() == (6, 6)


# Test creating a single, named op using the dictionary syntax. Document that annotation cannot be wrapped in a tuple for singleton case.
def test_multiout_single_entry():
    @op(out={"a": Out()})
    def single_output_op() -> int:
        return 5

    assert single_output_op() == 5
    result = execute_op_in_graph(single_output_op)
    assert result.output_for_node("single_output_op", "a") == 5


def test_tuple_named_single_output():
    # Ensure functionality in the case where you want to have a named tuple output
    @op(out={"a": Out()})
    def single_output_op_tuple() -> Tuple[int, int]:
        return (5, 5)

    assert single_output_op_tuple() == (5, 5)
    assert execute_op_in_graph(single_output_op_tuple).output_for_node(
        "single_output_op_tuple", "a"
    ) == (5, 5)


# Test creating a multi-out op with the incorrect annotation.
def test_op_multiout_incorrect_annotation():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Expected Tuple annotation for multiple outputs, but received non-tuple annotation.",
    ):

        @op(out={"a": Out(), "b": Out()})
        def _incorrect_annotation_op() -> int:
            return 1


def test_op_typing_annotations():
    @op
    def my_dict_op() -> Dict[str, int]:
        return {"foo": 5}

    assert my_dict_op() == {"foo": 5}

    my_output = {"foo": 5}, ("foo",)

    @op(out={"a": Out(), "b": Out()})
    def my_dict_multiout() -> Tuple[Dict[str, int], Tuple[str]]:
        return {"foo": 5}, ("foo",)

    assert my_dict_multiout() == my_output
    result = execute_op_in_graph(my_dict_multiout)
    assert result.output_for_node("my_dict_multiout", "a") == my_output[0]
    assert result.output_for_node("my_dict_multiout", "b") == my_output[1]


# Test simplest possible multiout case
def test_op_multiout_base():
    @op(out={"a": Out(), "b": Out()})
    def basic_multiout() -> Tuple[int, str]:
        return (5, "foo")

    assert basic_multiout() == (5, "foo")
    result = execute_op_in_graph(basic_multiout)
    assert result.output_for_node("basic_multiout", "a") == 5
    assert result.output_for_node("basic_multiout", "b") == "foo"


# Test tuple size mismatch (larger and smaller)
def test_op_multiout_size_mismatch():
    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Expected Tuple annotation to have number of entries matching the number of outputs "
            "for more than one output. Expected 2 outputs but annotation has 3."
        ),
    ):

        @op(out={"a": Out(), "b": Out()})
        def _basic_multiout_wrong_annotation() -> Tuple[int, int, int]:
            return (5, 5, 5)


# Document what happens when someone tries to use type annotations with Output
def test_type_annotations_with_output():
    @op
    def my_op_returns_output() -> Output:
        return Output(5)

    output = my_op_returns_output()
    assert output.value == 5
    result = execute_op_in_graph(my_op_returns_output)
    assert result.output_for_node("my_op_returns_output") == 5


# Document what happens when someone tries to use type annotations with generator
def test_type_annotations_with_generator():
    @op
    def my_op_yields_output() -> Generator[Output, None, None]:
        yield Output(5)

    assert list(my_op_yields_output())[0].value == 5
    result = execute_op_in_graph(my_op_yields_output)
    assert result.output_for_node("my_op_yields_output") == 5


def test_log_events():
    @op
    def basic_op(context):
        context.log_event(AssetMaterialization("first"))
        context.log_event(AssetMaterialization("second"))
        context.log_event(ExpectationResult(success=True))
        context.log_event(AssetObservation("fourth"))

    with instance_for_test() as instance:
        result = execute_op_in_graph(basic_op, instance=instance)
        asset_materialization_keys = [
            materialization.label
            for materialization in result.asset_materializations_for_node("basic_op")
        ]

        assert asset_materialization_keys == ["first", "second"]

        relevant_events_from_execution = [
            event
            for event in result.all_node_events
            if event.is_asset_observation
            or event.is_step_materialization
            or event.is_expectation_result
        ]

        relevant_events_from_event_log = [
            event_log.dagster_event
            for event_log in instance.all_logs(result.run_id)
            if event_log.dagster_event is not None
            and (
                event_log.dagster_event.is_asset_observation
                or event_log.dagster_event.is_step_materialization
                or event_log.dagster_event.is_expectation_result
            )
        ]

        def _assertions_from_event_list(events):
            assert events[0].is_step_materialization
            assert events[0].event_specific_data.materialization.label == "first"

            assert events[1].is_step_materialization
            assert events[1].event_specific_data.materialization.label == "second"

            assert events[2].is_expectation_result

            assert events[3].is_asset_observation

        _assertions_from_event_list(relevant_events_from_execution)

        _assertions_from_event_list(relevant_events_from_event_log)


def test_yield_event_ordering():
    @op
    def yielding_op(context):
        context.log_event(AssetMaterialization("first"))
        time.sleep(1)
        context.log.debug("A log")
        context.log_event(AssetMaterialization("second"))
        yield AssetMaterialization("third")
        yield Output("foo")

    with instance_for_test() as instance:
        result = execute_op_in_graph(yielding_op, instance=instance)

        assert result.success

        asset_materialization_keys = [
            materialization.label
            for materialization in result.asset_materializations_for_node("yielding_op")
        ]

        assert asset_materialization_keys == ["first", "second", "third"]

        relevant_event_logs = [
            event_log
            for event_log in instance.all_logs(result.run_id)
            if event_log.dagster_event is not None
            and (
                event_log.dagster_event.is_asset_observation
                or event_log.dagster_event.is_step_materialization
                or event_log.dagster_event.is_expectation_result
            )
        ]

        log_entries = [
            event_log
            for event_log in instance.all_logs(result.run_id)
            if event_log.dagster_event is None
        ]
        log = log_entries[0]
        assert log.user_message == "A log"

        first = relevant_event_logs[0]
        assert first.dagster_event.event_specific_data.materialization.label == "first"

        second = relevant_event_logs[1]
        assert second.dagster_event.event_specific_data.materialization.label == "second"

        third = relevant_event_logs[2]
        assert third.dagster_event.event_specific_data.materialization.label == "third"

        assert second.timestamp - first.timestamp >= 1
        assert log.timestamp - first.timestamp >= 1


def test_metadata_logging():
    @op
    def basic(context):
        context.add_output_metadata({"foo": "bar"})
        return "baz"

    result = execute_op_in_graph(basic)
    assert result.success
    assert result.output_for_node("basic") == "baz"
    events = result.events_for_node("basic")
    assert len(events[1].event_specific_data.metadata) == 1
    assert events[1].event_specific_data.metadata["foo"].text == "bar"


def test_metadata_logging_multiple_entries():
    @op
    def basic(context):
        context.add_output_metadata({"foo": "bar"})
        context.add_output_metadata({"baz": "bat"})

    with pytest.raises(
        DagsterInvariantViolationError,
        match="In op 'basic', attempted to log metadata for output 'result' more than once.",
    ):
        execute_op_in_graph(basic)


def test_log_event_multi_output():
    @op(out={"out1": Out(), "out2": Out()})
    def the_op(context):
        context.log_event(AssetMaterialization("foo"))
        yield Output(value=1, output_name="out1")
        context.log_event(AssetMaterialization("bar"))
        yield Output(value=2, output_name="out2")
        context.log_event(AssetMaterialization("baz"))

    result = execute_op_in_graph(the_op)
    assert result.success
    assert len(result.asset_materializations_for_node("the_op")) == 3


def test_log_metadata_multi_output():
    @op(out={"out1": Out(), "out2": Out()})
    def the_op(context):
        context.add_output_metadata({"foo": "bar"}, output_name="out1")
        yield Output(value=1, output_name="out1")
        context.add_output_metadata({"bar": "baz"}, output_name="out2")
        yield Output(value=2, output_name="out2")

    result = execute_op_in_graph(the_op)
    assert result.success
    events = result.events_for_node("the_op")
    first_output_event = events[1]
    second_output_event = events[3]

    assert "foo" in first_output_event.event_specific_data.metadata
    assert "bar" in second_output_event.event_specific_data.metadata


def test_log_metadata_after_output():
    @op
    def the_op(context):
        yield Output(1)
        context.add_output_metadata({"foo": "bar"})

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "In op 'the_op', attempted to log output metadata for output 'result' which has already"
            " been yielded. Metadata must be logged before the output is yielded."
        ),
    ):
        execute_op_in_graph(the_op)


def test_log_metadata_multiple_dynamic_outputs():
    @op(out={"out1": DynamicOut(), "out2": DynamicOut()})
    def the_op(context):
        context.add_output_metadata({"one": "one"}, output_name="out1", mapping_key="one")
        yield DynamicOutput(value=1, output_name="out1", mapping_key="one")
        context.add_output_metadata({"two": "two"}, output_name="out1", mapping_key="two")
        context.add_output_metadata({"three": "three"}, output_name="out2", mapping_key="three")
        yield DynamicOutput(value=2, output_name="out1", mapping_key="two")
        yield DynamicOutput(value=3, output_name="out2", mapping_key="three")
        context.add_output_metadata({"four": "four"}, output_name="out2", mapping_key="four")
        yield DynamicOutput(value=4, output_name="out2", mapping_key="four")

    result = execute_op_in_graph(the_op)
    assert result.success
    events = result.all_node_events
    output_event_one = events[1]
    assert output_event_one.event_specific_data.mapping_key == "one"
    assert "one" in output_event_one.event_specific_data.metadata
    output_event_two = events[3]
    assert output_event_two.event_specific_data.mapping_key == "two"
    assert "two" in output_event_two.event_specific_data.metadata
    output_event_three = events[5]
    assert output_event_three.event_specific_data.mapping_key == "three"
    assert "three" in output_event_three.event_specific_data.metadata
    output_event_four = events[7]
    assert output_event_four.event_specific_data.mapping_key == "four"
    assert "four" in output_event_four.event_specific_data.metadata


def test_log_metadata_after_dynamic_output():
    @op(out=DynamicOut())
    def the_op(context):
        yield DynamicOutput(1, mapping_key="one")
        context.add_output_metadata({"foo": "bar"}, mapping_key="one")

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "In op 'the_op', attempted to log output metadata for output 'result' with mapping_key"
            " 'one' which has already been yielded. Metadata must be logged before the output is"
            " yielded."
        ),
    ):
        execute_op_in_graph(the_op)


def test_args_kwargs_op():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"@op 'the_op' decorated function has positional vararg parameter "
        r"'\*_args'. @op decorated functions should only have keyword arguments "
        r"that match input names and, if system information is required, a "
        r"first positional parameter named 'context'.",
    ):

        @op(ins={"the_in": In()})
        def the_op(*_args):
            pass

    @op(ins={"the_in": In()})
    def the_op(**kwargs):  # noqa: F811
        return kwargs["the_in"]

    @op
    def emit_op():
        return 1

    @graph
    def the_graph_provides_inputs():
        the_op(emit_op())

    result = the_graph_provides_inputs.execute_in_process()
    assert result.success


def test_generic_output_op():
    @op
    def the_op() -> Output[str]:
        return Output("foo")

    assert the_op.output_def_named("result").dagster_type.key == "String"

    result = execute_op_in_graph(the_op)
    assert result.success
    assert result.output_for_node("the_op") == "foo"

    result = the_op()
    assert isinstance(result, Output)
    assert result.value == "foo"

    @op
    def the_op_bad_type_match() -> Output[int]:
        return Output("foo")  # type: ignore  # (test error)

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match=(
            'Type check failed for step output "result" - expected type '
            '"Int". Description: Value "foo" of python type "str" must be a int.'
        ),
    ):
        execute_op_in_graph(the_op_bad_type_match)

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match=(
            'Type check failed for op "the_op_bad_type_match" output "result" - expected type '
            '"Int". Description: Value "foo" of python type "str" must be a int.'
        ),
    ):
        the_op_bad_type_match()


def test_output_generic_correct_inner_type():
    @op
    def the_op_not_using_output() -> Output[int]:
        return 42  # type: ignore  # (test error)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            'Error with output for op "the_op_not_using_output": output '
            "'result' has generic Output annotation, but did not receive Output "
            "object for this output."
        ),
    ):
        execute_op_in_graph(the_op_not_using_output)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "output 'result' has generic Output annotation, but did not "
            "receive Output object for this output."
        ),
    ):
        the_op_not_using_output()

    @op
    def the_op_annotation_not_using_output() -> int:
        return Output(42)  # type: ignore  # (test error)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "received Output object for output 'result' which does not have an Output annotation."
        ),
    ):
        execute_op_in_graph(the_op_annotation_not_using_output)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "received Output object for output 'result' which does not have an Output annotation."
        ),
    ):
        the_op_annotation_not_using_output()


def test_generic_output_tuple_op():
    @op(out={"out1": Out(), "out2": Out()})
    def the_op() -> Tuple[Output[str], Output[int]]:
        return (Output("foo"), Output(5))

    result = execute_op_in_graph(the_op)
    assert result.success

    result1, result2 = the_op()
    assert isinstance(result1, Output)
    assert result1.value == "foo"
    assert isinstance(result2, Output)
    assert result2.value == 5

    @op(out={"out1": Out(), "out2": Out()})
    def the_op_bad_type_match() -> Tuple[Output[str], Output[int]]:
        return (Output("foo"), Output("foo"))  # type: ignore

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match=(
            'Type check failed for step output "out2" - expected type "Int". '
            'Description: Value "foo" of python type "str" must be a int.'
        ),
    ):
        execute_op_in_graph(the_op_bad_type_match)

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match=(
            'Type check failed for op "the_op_bad_type_match" output "out2" - '
            'expected type "Int". Description: Value "foo" of python type "str" '
            "must be a int."
        ),
    ):
        the_op_bad_type_match()


def test_generic_output_tuple_complex_types():
    @op(out={"out1": Out(), "out2": Out()})
    def the_op() -> Tuple[Output[List[str]], Output[Dict[str, str]]]:
        return (Output(["foo"]), Output({"foo": "bar"}))

    result = execute_op_in_graph(the_op)
    assert result.success

    result1, result2 = the_op()
    assert isinstance(result1, Output)
    assert isinstance(result2, Output)

    assert result1.value == ["foo"]
    assert result2.value == {"foo": "bar"}


def test_generic_output_name_mismatch():
    @op(out={"out1": Out(), "out2": Out()})
    def the_op() -> Tuple[Output[int], Output[str]]:
        return Output(42, output_name="out2"), Output("foo", output_name="out1")

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Output was explicitly named 'out2', which does not match the "
            "output definition specified for position 0: 'out1'."
        ),
    ):
        execute_op_in_graph(the_op)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Output was explicitly named 'out2', which does not match the "
            "output definition specified for position 0: 'out1'."
        ),
    ):
        the_op()


def test_generic_dynamic_output():
    @op
    def basic() -> List[DynamicOutput[int]]:
        return [
            DynamicOutput(mapping_key="1", value=1),
            DynamicOutput(mapping_key="2", value=2),
        ]

    result = execute_op_in_graph(basic)
    assert result.success
    assert result.output_for_node("basic") == {"1": 1, "2": 2}

    result = basic()
    assert len(result) == 2
    out1, out2 = result
    assert out1.value == 1
    assert out2.value == 2


def test_generic_dynamic_output_type_mismatch():
    @op
    def basic() -> List[DynamicOutput[int]]:
        return [
            DynamicOutput(mapping_key="1", value=1),
            DynamicOutput(mapping_key="2", value="2"),  # type: ignore
        ]

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match=(
            'Type check failed for step output "result" - expected type '
            '"Int". Description: Value "2" of python type "str" must be a int.'
        ),
    ):
        execute_op_in_graph(basic)

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match=(
            'Type check failed for op "basic" output "result" - expected type '
            '"Int". Description: Value "2" of python type "str" must be a int.'
        ),
    ):
        basic()


def test_generic_dynamic_output_mix_with_regular():
    @op(out={"regular": Out(), "dynamic": DynamicOut()})
    def basic() -> Tuple[Output[int], List[DynamicOutput[str]]]:
        return (
            Output(5),
            [
                DynamicOutput(mapping_key="1", value="foo"),
                DynamicOutput(mapping_key="2", value="bar"),
            ],
        )

    result = execute_op_in_graph(basic)
    assert result.success

    assert result.output_for_node("basic", "regular") == 5
    assert result.output_for_node("basic", "dynamic") == {"1": "foo", "2": "bar"}

    non_dynamic, dynamic = basic()
    assert isinstance(non_dynamic, Output)
    assert non_dynamic.value == 5
    assert isinstance(dynamic, list)
    d_out1, d_out2 = dynamic
    assert d_out1.value == "foo"
    assert d_out2.value == "bar"


def test_generic_dynamic_output_mix_with_regular_type_mismatch():
    @op(out={"regular": Out(), "dynamic": DynamicOut()})
    def basic() -> Tuple[Output[int], List[DynamicOutput[str]]]:
        return (
            Output(5),
            [
                DynamicOutput(mapping_key="1", value="foo"),
                DynamicOutput(mapping_key="2", value=5),  # type: ignore
            ],
        )

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match=(
            'Type check failed for step output "dynamic" - expected type '
            '"String". Description: Value "5" of python type "int" must be a string.'
        ),
    ):
        execute_op_in_graph(basic)

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match=(
            'Type check failed for op "basic" output "dynamic" - expected '
            'type "String". Description: Value "5" of python type "int" must be a string.'
        ),
    ):
        basic()


def test_generic_dynamic_output_name_not_provided():
    @op
    def basic() -> List[DynamicOutput[int]]:
        return [DynamicOutput(value=5, mapping_key="blah", output_name="blah")]

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Output was explicitly named 'blah', which does not match the "
            "output definition specified for position 0: 'result'."
        ),
    ):
        execute_op_in_graph(basic)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Output was explicitly named 'blah', which does not match the "
            "output definition specified for position 0: 'result'."
        ),
    ):
        basic()


def test_generic_dynamic_output_name_mismatch():
    @op(out={"the_name": DynamicOut()})
    def basic() -> List[DynamicOutput[int]]:
        return [DynamicOutput(value=5, mapping_key="blah", output_name="bad_name")]

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Output was explicitly named 'bad_name', which does not match the "
            "output definition specified for position 0: 'the_name'."
        ),
    ):
        execute_op_in_graph(basic)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Output was explicitly named 'bad_name', which does not match the "
            "output definition specified for position 0: 'the_name'."
        ),
    ):
        basic()


def test_generic_dynamic_output_bare_list():
    @op
    def basic() -> List[DynamicOutput]:
        return [DynamicOutput(4, mapping_key="1")]

    result = execute_op_in_graph(basic)
    assert result.success
    assert result.output_for_node("basic") == {"1": 4}

    result = basic()
    assert isinstance(result, list)
    assert result[0].value == 4


def test_generic_dynamic_output_bare():
    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Op annotated with return type DynamicOutput. DynamicOutputs can "
            "only be returned in the context of a List. If only one output is "
            "needed, use the Output API."
        ),
    ):

        @op
        def basic() -> DynamicOutput:  # type: ignore
            pass

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Op annotated with return type DynamicOutput. DynamicOutputs can "
            "only be returned in the context of a List. If only one output is "
            "needed, use the Output API."
        ),
    ):

        @op
        def another_basic() -> DynamicOutput[int]:  # type: ignore
            pass


def test_generic_dynamic_output_empty():
    @op
    def basic() -> List[DynamicOutput]:
        return []

    result = execute_op_in_graph(basic)
    assert result.success

    with pytest.raises(
        DagsterInvariantViolationError,
        match="No outputs found for output 'result' from node 'basic'.",
    ):
        result.output_for_node("basic")

    result = basic()
    assert isinstance(result, list)

    @op(out=DynamicOut())
    def dynamic_op_no_return_or_yield():
        pass

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            r"dynamic output 'result' expected a list of DynamicOutput objects, but instead"
            r" received instead an object of type \<class 'NoneType'\>\."
        ),
    ):
        execute_op_in_graph(dynamic_op_no_return_or_yield)

    # Ensure that invocation behavior matches
    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            r"dynamic output 'result' expected a list of DynamicOutput objects, but instead"
            r" received instead an object of type \<class 'NoneType'\>\."
        ),
    ):
        dynamic_op_no_return_or_yield()


def test_dynamic_output_yields_no_outputs():
    @op(out=DynamicOut())
    def the_op():
        yield AssetMaterialization("third")

    result = execute_op_in_graph(the_op)
    assert result.success

    assert len(list(the_op())) == 1


def test_generic_dynamic_output_empty_with_type():
    @op
    def basic() -> List[DynamicOutput[str]]:
        return []

    result = execute_op_in_graph(basic)
    assert result.success

    # Equivalent behavior in the dynamic yield case. is_required doesn't
    # actually do anything on a DynamicOut right now:
    # https://github.com/dagster-io/dagster/issues/5948#issuecomment-997037163
    @op(out=DynamicOut(dagster_type=str, is_required=False))
    def basic_yield():
        pass

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "dynamic output 'result' expected a list of DynamicOutput "
            "objects, but instead received instead an object of type "
            "<class 'NoneType'>."
        ),
    ):
        execute_op_in_graph(basic_yield)

    # Ensure that invocation behavior matches
    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "dynamic output 'result' expected a list of DynamicOutput "
            "objects, but instead received instead an object of type "
            "<class 'NoneType'>."
        ),
    ):
        basic_yield()


def test_generic_dynamic_multiple_outputs_empty():
    @op(out={"out1": Out(), "out2": DynamicOut()})
    def basic() -> Tuple[Output, List[DynamicOutput]]:
        return (Output(5), [])

    result = execute_op_in_graph(basic)
    assert result.success

    with pytest.raises(
        DagsterInvariantViolationError,
        match="No outputs found for output 'out2' from node 'basic'.",
    ):
        result.output_for_node("basic", "out2")

    out1, out2 = basic()
    assert isinstance(out1, Output)
    assert isinstance(out2, list)


def test_non_dynamic_empty_list():
    @op(
        out={
            "output_1": Out(List[Dict]),
            "output_2": Out(List[Dict]),
        }
    )
    def dummy_op():
        output_1 = [{"dummy_key1": "dummy_value1"}, {"dummy_key2": "dummy_value2"}]
        output_2 = []
        return (output_1, output_2)

    result = execute_op_in_graph(dummy_op)
    assert result.success


def test_required_io_manager_op_access():
    # Show that required io manager keys can be accessed from within the body
    # of an op.
    @op(out=Out(io_manager_key="foo"))
    def the_op(context):
        assert hasattr(context.resources, "foo")

    @job(resource_defs={"foo": mem_io_manager})
    def the_job():
        the_op()

    result = the_job.execute_in_process()
    assert result.success


def test_dynamic_output_bad_list_entry():
    @op
    def basic() -> List[DynamicOutput[int]]:
        return ["foo"]  # type: ignore

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Error with output for op \"basic\": dynamic output 'result' at position 0 expected a"
            " list of DynamicOutput objects, but received an item with type <class 'str'>."
        ),
    ):
        execute_op_in_graph(basic)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Error with output for op \"basic\": dynamic output 'result' at position 0 expected a"
            " list of DynamicOutput objects, but received an item with type <class 'str'>."
        ),
    ):
        basic()

    @op(out={"out1": Out(), "out2": DynamicOut()})
    def basic_multi_output() -> Tuple[Output[int], List[DynamicOutput[str]]]:
        return (5, ["foo"])  # type: ignore

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Error with output for op \"basic_multi_output\": output 'out1' "
            "has generic Output annotation, but did not receive Output object "
            "for this output. Received instead an object of type <class 'int'>."
        ),
    ):
        execute_op_in_graph(basic_multi_output)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Error with output for op \"basic_multi_output\": output 'out1' "
            "has generic Output annotation, but did not receive Output object "
            "for this output. Received instead an object of type <class 'int'>."
        ),
    ):
        basic_multi_output()


def test_list_out_op():
    @op(out={"list_out": Out(List[str]), "other_out": Out(int)})
    def test_op() -> Tuple[List[str], int]:
        return ([], 5)

    result = execute_op_in_graph(test_op)
    assert result.success

    assert test_op() == ([], 5)


def test_dynamic_list_out_no_annotation():
    @op(out=DynamicOut())
    def the_op():
        return [DynamicOutput(5, mapping_key="foo")]

    result = execute_op_in_graph(the_op)
    assert result.success

    assert len(the_op()) == 1


def test_output_return_no_annotation():
    @op
    def the_op():
        return Output(5)

    assert execute_op_in_graph(the_op).success
    assert the_op() == Output(5)


def test_output_mismatch_tuple_lengths():
    @op(out={"out1": Out(), "out2": Out()})
    def the_op() -> Tuple[int, int]:
        return (1, 2, 3)  # type: ignore  # (test error)

    with pytest.raises(DagsterInvariantViolationError, match="Length mismatch"):
        execute_op_in_graph(the_op)

    with pytest.raises(DagsterInvariantViolationError, match="Length mismatch"):
        the_op()


def test_none_annotated_input():
    with pytest.raises(DagsterInvalidDefinitionError, match="is annotated with Nothing"):

        @op
        def op1(input1: None):
            ...


def test_default_code_version():
    @op(code_version="foo", out={"a": Out(), "b": Out(code_version="bar")})
    def alpha():
        yield Output(1, "a")
        yield Output(1, "b")

    assert alpha.output_def_named("a").code_version == "foo"
    assert alpha.output_def_named("b").code_version == "bar"


def test_colliding_args():
    # ensure errors for argument collision, for normal python functions these raise as TypeError

    @op
    def emit():
        return 1

    @op
    def foo(x, y):
        print(x, y)  # noqa: T201

    # in composition
    with pytest.raises(
        DagsterInvalidInvocationError, match="op foo got multiple values for argument 'x'"
    ):

        @graph
        def collide():
            x = emit()
            foo_2 = partial(foo, x=x)
            foo_2(emit())

    @op
    def bar(x, y=2):
        print(x, y)  # noqa: T201

    # or direct invocation
    with pytest.raises(
        DagsterInvalidInvocationError, match="op bar got multiple values for argument 'x'"
    ):
        bar_2 = partial(bar, x=1)
        bar_2(1)
