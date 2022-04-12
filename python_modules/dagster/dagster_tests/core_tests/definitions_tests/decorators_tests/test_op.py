import time
from typing import Dict, Generator, List, Tuple

import pytest

from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DagsterType,
    DagsterTypeCheckDidNotPass,
    DynamicOut,
    DynamicOutput,
    ExpectationResult,
    In,
    Materialization,
    Nothing,
    Out,
    Output,
    SolidDefinition,
    build_op_context,
    graph,
    op,
    solid,
)
from dagster.core.definitions.op_definition import OpDefinition
from dagster.core.test_utils import instance_for_test
from dagster.core.types.dagster_type import Int, String


def execute_op_in_graph(an_op, instance=None):
    @graph
    def my_graph():
        an_op()

    result = my_graph.execute_in_process(instance=instance)
    return result


def test_op():
    @op
    def my_op():
        pass

    assert isinstance(my_op, OpDefinition)
    execute_op_in_graph(my_op)


def test_solid_decorator_produces_solid():
    @solid
    def my_solid():
        pass

    assert isinstance(my_solid, SolidDefinition) and not isinstance(my_solid, OpDefinition)


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
        return 1

    assert my_op.outs == {
        "result": Out(
            metadata={"x": 1}, dagster_type=Int, is_required=True, io_manager_key="io_manager"
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
    @op(out={"a": Out(metadata={"x": 1}), "b": Out(metadata={"y": 2})})
    def my_op() -> Tuple[int, str]:
        return 1, "q"

    assert len(my_op.output_defs) == 2

    assert my_op.outs == {
        "a": Out(
            metadata={"x": 1}, dagster_type=Int, is_required=True, io_manager_key="io_manager"
        ),
        "b": Out(
            metadata={"y": 2}, dagster_type=String, is_required=True, io_manager_key="io_manager"
        ),
    }
    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"

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
    @op(out={"a": Out(metadata={"x": 1}, is_required=False), "b": Out(metadata={"y": 2})})
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
            pass


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
        match="Expected Tuple annotation to have number of entries matching the number of outputs "
        "for more than one output. Expected 2 outputs but annotation has 3.",
    ):

        @op(out={"a": Out(), "b": Out()})
        def _basic_multiout_wrong_annotation() -> Tuple[int, int, int]:
            pass


# Document what happens when someone tries to use type annotations with Output
def test_type_annotations_with_output():
    @op
    def my_op_returns_output() -> Output:
        return Output(5)

    with pytest.raises(DagsterTypeCheckDidNotPass):
        my_op_returns_output()


# Document what happens when someone tries to use type annotations with generator
def test_type_annotations_with_generator():
    @op
    def my_op_yields_output() -> Generator[Output, None, None]:
        yield Output(5)

    assert list(my_op_yields_output())[0].value == 5
    result = execute_op_in_graph(my_op_yields_output)
    assert result.output_for_node("my_op_yields_output") == 5


def test_op_config_entry_collision():
    @op(config_schema={"foo": str})
    def my_op(_):
        pass

    @graph
    def my_graph():
        my_op()
        my_op.alias("my_op2")()

    my_job = my_graph.to_job()

    with pytest.raises(DagsterInvalidConfigError, match="Received both field"):
        my_job.execute_in_process(
            run_config={
                "solids": {"my_op": {"config": {"foo": "bar"}}},
                "ops": {"my_op2": {"config": {"foo": "bar"}}},
            }
        )

    @graph
    def nest_collision():
        my_graph()

    my_nested_graph_job = nest_collision.to_job()

    with pytest.raises(
        DagsterInvalidConfigError,
        match="Received both field 'ops' and field 'solids' in config. Please use one or the other.",
    ):
        my_nested_graph_job.execute_in_process(
            run_config={
                "ops": {
                    "my_graph": {
                        "solids": {"my_op": {"config": {"foo": "bar"}}},
                        "ops": {"my_op2": {"config": {"foo": "bar"}}},
                    }
                }
            }
        )


def test_solid_and_op_config_error_messages():
    @op(config_schema={"foo": str})
    def my_op(context):
        return context.op_config["foo"]

    @graph
    def my_graph():
        my_op()

    with pytest.raises(
        DagsterInvalidConfigError,
        match='Missing required config entry "ops" at the root. Sample config for missing '
        "entry: {'ops': {'my_op': {'config': {'foo': '...'}}}}",
    ):
        my_graph.execute_in_process()

    @solid(config_schema={"foo": str})
    def my_solid(context):
        return context.solid_config["foo"]

    @graph
    def my_graph_with_solid():
        my_solid()

    # Document that for now, using jobs at the top level will result in config errors being
    # in terms of ops.
    with pytest.raises(
        DagsterInvalidConfigError,
        match='Missing required config entry "ops" at the root. Sample config for missing '
        "entry: {'ops': {'my_solid': {'config': {'foo': '...'"
        "}}}}",
    ):
        my_graph_with_solid.to_job().execute_in_process()


def test_error_message_mixed_ops_and_solids():
    # Document that opting into using job at the top level (even one op) will switch error messages at the top level
    # to ops.

    @op(config_schema={"foo": str})
    def my_op(context):
        return context.op_config["foo"]

    @solid(config_schema={"foo": str})
    def my_solid(context):
        return context.solid_config["foo"]

    @graph
    def my_graph_with_both():
        my_op()
        my_solid()

    my_job = my_graph_with_both.to_job()

    with pytest.raises(
        DagsterInvalidConfigError,
        match='Missing required config entry "ops" at the root. Sample config for missing '
        "entry: {'ops': {'my_op': {'config': {'foo': '...'}}, 'my_solid': "
        "{'config': {'foo': '...'}}}",
    ):
        my_job.execute_in_process()

    @graph
    def nested_ops():
        my_graph_with_both()

    nested_job = nested_ops.to_job()

    with pytest.raises(
        DagsterInvalidConfigError,
        match='Missing required config entry "ops" at the root. Sample config for missing '
        "entry: {'ops': {'my_graph_with_both': {'ops': {'my_op': {'config': {'foo': '...'}}, 'my_solid': "
        "{'config': {'foo': '...'}}}}}",
    ):
        nested_job.execute_in_process()


def test_log_events():
    @op
    def basic_op(context):
        context.log_event(AssetMaterialization("first"))
        context.log_event(Materialization("second"))
        context.log_event(AssetMaterialization("third"))
        context.log_event(ExpectationResult(success=True))
        context.log_event(AssetObservation("fourth"))

    with instance_for_test() as instance:
        result = execute_op_in_graph(basic_op, instance=instance)
        asset_materialization_keys = [
            materialization.label
            for materialization in result.asset_materializations_for_node("basic_op")
        ]

        assert asset_materialization_keys == ["first", "second", "third"]

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

            assert events[2].is_step_materialization
            assert events[2].event_specific_data.materialization.label == "third"

            assert events[3].is_expectation_result

            assert events[4].is_asset_observation

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
    assert len(events[1].event_specific_data.metadata_entries) == 1
    metadata_entry = events[1].event_specific_data.metadata_entries[0]
    assert metadata_entry.label == "foo"
    assert metadata_entry.entry_data.text == "bar"


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

    assert first_output_event.event_specific_data.metadata_entries[0].label == "foo"
    assert second_output_event.event_specific_data.metadata_entries[0].label == "bar"


def test_log_metadata_after_output():
    @op
    def the_op(context):
        yield Output(1)
        context.add_output_metadata({"foo": "bar"})

    with pytest.raises(
        DagsterInvariantViolationError,
        match="In op 'the_op', attempted to log output metadata for output 'result' which has already been yielded. Metadata must be logged before the output is yielded.",
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
    assert output_event_one.event_specific_data.metadata_entries[0].label == "one"
    output_event_two = events[3]
    assert output_event_two.event_specific_data.mapping_key == "two"
    assert output_event_two.event_specific_data.metadata_entries[0].label == "two"
    output_event_three = events[5]
    assert output_event_three.event_specific_data.mapping_key == "three"
    assert output_event_three.event_specific_data.metadata_entries[0].label == "three"
    output_event_four = events[7]
    assert output_event_four.event_specific_data.mapping_key == "four"
    assert output_event_four.event_specific_data.metadata_entries[0].label == "four"


def test_log_metadata_after_dynamic_output():
    @op(out=DynamicOut())
    def the_op(context):
        yield DynamicOutput(1, mapping_key="one")
        context.add_output_metadata({"foo": "bar"}, mapping_key="one")

    with pytest.raises(
        DagsterInvariantViolationError,
        match="In op 'the_op', attempted to log output metadata for output 'result' with mapping_key 'one' which has already been yielded. Metadata must be logged before the output is yielded.",
    ):
        execute_op_in_graph(the_op)


def test_log_metadata_asset_materialization():
    key = AssetKey(["foo"])

    @op(out=Out(asset_key=key))
    def the_op(context):
        context.add_output_metadata({"bar": "baz"})
        return 5

    result = execute_op_in_graph(the_op)
    materialization = result.asset_materializations_for_node("the_op")[0]
    assert len(materialization.metadata_entries) == 1
    assert materialization.metadata_entries[0].label == "bar"
    assert materialization.metadata_entries[0].entry_data.text == "baz"


def test_implicit_op_output_with_asset_key():
    @op(out=Out(asset_key=AssetKey("my_dataset")))
    def my_constant_asset_op():
        return 5

    result = execute_op_in_graph(my_constant_asset_op)
    assert result.success
    assert len(result.asset_materializations_for_node(my_constant_asset_op.name)) == 1


def test_args_kwargs_op():
    # pylint: disable=function-redefined
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"@op 'the_op' decorated function has positional vararg parameter "
        r"'\*args'. @op decorated functions should only have keyword arguments "
        r"that match input names and, if system information is required, a "
        r"first positional parameter named 'context'.",
    ):

        @op(ins={"the_in": In()})
        def the_op(*_args):
            pass

    @op(ins={"the_in": In()})
    def the_op(**kwargs):
        return kwargs["the_in"]

    @op
    def emit_op():
        return 1

    @graph
    def the_graph_provides_inputs():
        the_op(emit_op())

    result = the_graph_provides_inputs.execute_in_process()
    assert result.success
