import re
import typing

import pytest

from dagster import (
    DagsterEventType,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
    Failure,
    In,
    Int,
    List,
    MetadataEntry,
    Optional,
    Out,
    String,
    Tuple,
    TypeCheck,
    check_dagster_type,
    fs_io_manager,
    job,
    make_python_type_usable_as_dagster_type,
    op,
    resource,
)
from dagster._core.types.dagster_type import (
    DagsterType,
    ListType,
    PythonObjectDagsterType,
    resolve_dagster_type,
)


class BarObj:
    pass


class _Bar(PythonObjectDagsterType):
    def __init__(self):
        super(_Bar, self).__init__(BarObj, name="Bar", description="A bar.")


Bar = _Bar()


def test_python_object_type():
    type_bar = Bar

    assert type_bar.unique_name == "Bar"
    assert type_bar.description == "A bar."
    assert_success(type_bar, BarObj())

    assert_failure(type_bar, None)

    assert_failure(type_bar, "not_a_bar")


def test_python_object_union_type():
    ntype = PythonObjectDagsterType(python_type=(int, float))
    assert ntype.unique_name == "Union[int, float]"
    assert_success(ntype, 1)
    assert_success(ntype, 1.5)
    assert_failure(ntype, "a")


def test_python_object_type_with_custom_type_check():
    def eq_3(_, value):
        return isinstance(value, int) and value == 3

    Int3 = DagsterType(name="Int3", type_check_fn=eq_3)

    assert Int3.unique_name == "Int3"
    assert check_dagster_type(Int3, 3).success
    assert not check_dagster_type(Int3, 5).success


def test_tuple_union_typing_type():

    UnionType = PythonObjectDagsterType(python_type=(str, int, float))

    assert UnionType.typing_type == typing.Union[str, int, float]


def test_nullable_python_object_type():
    assert check_dagster_type(Optional[Bar], BarObj()).success
    assert check_dagster_type(Optional[Bar], None).success
    assert not check_dagster_type(Optional[Bar], "not_a_bar").success


def test_nullable_int_coercion():
    assert check_dagster_type(Int, 1).success
    assert not check_dagster_type(Int, None).success

    assert check_dagster_type(Optional[Int], 1).success
    assert check_dagster_type(Optional[Int], None).success


def assert_type_check(type_check):
    assert isinstance(type_check, TypeCheck) and type_check.success


def assert_success(dagster_type, value):
    type_check_result = dagster_type.type_check(None, value)
    assert_type_check(type_check_result)


def assert_failure(dagster_type, value):
    res = dagster_type.type_check(None, value)
    assert not res.success


def test_nullable_list_combos_coerciion():
    assert not check_dagster_type(List[Int], None).success
    assert check_dagster_type(List[Int], []).success
    assert check_dagster_type(List[Int], [1]).success
    assert not check_dagster_type(List[Int], [None]).success

    assert check_dagster_type(Optional[List[Int]], None).success
    assert check_dagster_type(Optional[List[Int]], []).success
    assert check_dagster_type(Optional[List[Int]], [1]).success
    assert not check_dagster_type(Optional[List[Int]], [None]).success

    assert not check_dagster_type(List[Optional[Int]], None).success
    assert check_dagster_type(List[Optional[Int]], []).success
    assert check_dagster_type(List[Optional[Int]], [1]).success
    assert check_dagster_type(List[Optional[Int]], [None]).success

    assert check_dagster_type(Optional[List[Optional[Int]]], None).success
    assert check_dagster_type(Optional[List[Optional[Int]]], []).success
    assert check_dagster_type(Optional[List[Optional[Int]]], [1]).success
    assert check_dagster_type(Optional[List[Optional[Int]]], [None]).success


def execute_no_throw(pipeline_def):
    return pipeline_def.execute_in_process(raise_on_error=False)


def _type_check_data_for_input(result, op_name, input_name):
    events_for_op = result.events_for_node(op_name)
    step_input_event = [
        event
        for event in events_for_op
        if event.event_type == DagsterEventType.STEP_INPUT
        and event.step_handle.to_key() == op_name
        and event.event_specific_data.input_name == input_name
    ][0]
    return step_input_event.event_specific_data.type_check_data


def test_input_types_succeed_in_pipeline():
    @op
    def return_one():
        return 1

    @op(ins={"num": In(int)})
    def take_num(num):
        return num

    @job
    def pipe():
        take_num(return_one())

    pipeline_result = pipe.execute_in_process()
    assert pipeline_result.success

    type_check_data = _type_check_data_for_input(
        pipeline_result, op_name="take_num", input_name="num"
    )
    assert type_check_data.success


def test_output_types_succeed_in_pipeline():
    @op(out=Out(int))
    def return_one():
        return 1

    @job
    def pipe():
        return_one()

    pipeline_result = pipe.execute_in_process()
    assert pipeline_result.success

    events_for_node = pipeline_result.events_for_node("return_one")
    output_event = [
        event for event in events_for_node if event.event_type == DagsterEventType.STEP_OUTPUT
    ].pop()

    type_check_data = output_event.event_specific_data.type_check_data
    assert type_check_data.success


def test_input_types_fail_in_pipeline():
    @op
    def return_one():
        return 1

    @op(ins={"string": In(str)})
    def take_string(string):
        return string

    @job
    def pipe():
        take_string(return_one())

    with pytest.raises(DagsterTypeCheckDidNotPass):
        pipe.execute_in_process()

    # now check events in no throw case

    pipeline_result = execute_no_throw(pipe)

    assert not pipeline_result.success

    type_check_data = _type_check_data_for_input(
        pipeline_result, op_name="take_string", input_name="string"
    )
    assert not type_check_data.success
    assert type_check_data.description == 'Value "1" of python type "int" must be a string.'

    failure_event = [
        event
        for event in pipeline_result.events_for_node("take_string")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()
    assert failure_event.step_failure_data.error.cls_name == "DagsterTypeCheckDidNotPass"


def test_output_types_fail_in_pipeline():
    @op(out=Out(str))
    def return_int_fails():
        return 1

    @job
    def pipe():
        return_int_fails()

    with pytest.raises(DagsterTypeCheckDidNotPass):
        pipe.execute_in_process()

    pipeline_result = execute_no_throw(pipe)

    assert not pipeline_result.success

    events_for_node = pipeline_result.events_for_node("return_int_fails")
    output_event = [
        event for event in events_for_node if event.event_type == DagsterEventType.STEP_OUTPUT
    ].pop()

    type_check_data = output_event.event_specific_data.type_check_data
    assert not type_check_data.success
    assert type_check_data.description == 'Value "1" of python type "int" must be a string.'

    failure_event = [
        event
        for event in pipeline_result.events_for_node("return_int_fails")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()

    assert failure_event.step_failure_data.error.cls_name == "DagsterTypeCheckDidNotPass"


# TODO add more step output use cases


class AlwaysFailsException(Exception):
    # Made to make exception explicit so that we aren't accidentally masking other Exceptions
    pass


def _always_fails(_, _value):
    raise AlwaysFailsException("kdjfkjd")


ThrowsExceptionType = DagsterType(
    name="ThrowsExceptionType",
    type_check_fn=_always_fails,
)


def _return_bad_value(_, _value):
    return "foo"


BadType = DagsterType(name="BadType", type_check_fn=_return_bad_value)


def test_input_type_returns_wrong_thing():
    @op
    def return_one():
        return 1

    @op(ins={"value": In(BadType)})
    def take_bad_thing(value):
        return value

    @job
    def pipe():
        take_bad_thing(return_one())

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape("You have returned 'foo' of type <")
        + "(class|type)"
        + re.escape(
            " 'str'> from the type check function of type \"BadType\". Return value must be instance of "
            "TypeCheck or a bool."
        ),
    ):
        pipe.execute_in_process()

    pipeline_result = execute_no_throw(pipe)
    assert not pipeline_result.success

    failure_event = [
        event
        for event in pipeline_result.events_for_node("take_bad_thing")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()

    assert failure_event.step_failure_data.error.cls_name == "DagsterInvariantViolationError"


def test_output_type_returns_wrong_thing():
    @op(out=Out(BadType))
    def return_one_bad_thing():
        return 1

    @job
    def pipe():
        return_one_bad_thing()

    with pytest.raises(DagsterInvariantViolationError):
        pipe.execute_in_process()

    pipeline_result = execute_no_throw(pipe)
    assert not pipeline_result.success

    failure_event = [
        event
        for event in pipeline_result.events_for_node("return_one_bad_thing")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()
    assert failure_event.step_failure_data.error.cls_name == "DagsterInvariantViolationError"


def test_input_type_throw_arbitrary_exception():
    @op
    def return_one():
        return 1

    @op(ins={"value": In(ThrowsExceptionType)})
    def take_throws(value):
        return value

    @job
    def pipe():
        take_throws(return_one())

    with pytest.raises(AlwaysFailsException):
        pipe.execute_in_process()

    pipeline_result = execute_no_throw(pipe)
    assert not pipeline_result.success
    failure_event = [
        event
        for event in pipeline_result.events_for_node("take_throws")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()
    assert failure_event.step_failure_data.error.cause.cls_name == "AlwaysFailsException"


def test_output_type_throw_arbitrary_exception():
    @op(out=Out(ThrowsExceptionType))
    def return_one_throws():
        return 1

    @job
    def pipe():
        return_one_throws()

    with pytest.raises(AlwaysFailsException):
        pipe.execute_in_process()

    pipeline_result = execute_no_throw(pipe)
    assert not pipeline_result.success
    failure_event = [
        event
        for event in pipeline_result.events_for_node("return_one_throws")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()
    assert failure_event.step_failure_data.error.cause.cls_name == "AlwaysFailsException"
    assert "kdjfkjd" in failure_event.step_failure_data.error.cause.message


def define_custom_dict(name, permitted_key_names):
    def type_check_method(_, value):
        if not isinstance(value, dict):
            return TypeCheck(
                False,
                description="Value {value} should be of type {type_name}.".format(
                    value=value, type_name=name
                ),
            )
        for key in value:
            if not key in permitted_key_names:
                return TypeCheck(
                    False,
                    description=(
                        "Key {name} is not a permitted value, values can only be of: " "{name_list}"
                    ).format(name=value.name, name_list=permitted_key_names),
                )
        return TypeCheck(
            True,
            metadata_entries=[
                MetadataEntry("row_count", value=str(len(value))),
                MetadataEntry("series_names", value=", ".join(value.keys())),
            ],
        )

    return DagsterType(key=name, name=name, type_check_fn=type_check_method)


def test_fan_in_custom_types_with_storage():
    CustomDict = define_custom_dict("CustomDict", ["foo", "bar"])

    @op(out=Out(CustomDict))
    def return_dict_1(_context):
        return {"foo": 3}

    @op(out=Out(CustomDict))
    def return_dict_2(_context):
        return {"bar": "zip"}

    @op(ins={"dicts": In(List[CustomDict])})
    def get_foo(_context, dicts):
        return dicts[0]["foo"]

    @job(resource_defs={"io_manager": fs_io_manager})
    def dict_job():
        # Fan-in
        get_foo([return_dict_1(), return_dict_2()])

    pipeline_result = dict_job.execute_in_process()
    assert pipeline_result.success


ReturnBoolType = DagsterType(name="ReturnBoolType", type_check_fn=lambda _, _val: True)


def test_return_bool_type():
    @op(out=Out(ReturnBoolType))
    def return_always_pass_bool_type(_):
        return 1

    @job
    def bool_type_job():
        return_always_pass_bool_type()

    assert bool_type_job.execute_in_process().success


def test_raise_on_error_type_check_returns_false():
    FalsyType = DagsterType(name="FalsyType", type_check_fn=lambda _, _val: False)

    @op(out=Out(FalsyType))
    def foo_op(_):
        return 1

    @job
    def foo_job():
        foo_op()

    with pytest.raises(DagsterTypeCheckDidNotPass):
        foo_job.execute_in_process()

    pipeline_result = foo_job.execute_in_process(raise_on_error=False)
    assert not pipeline_result.success
    assert [event.event_type_value for event in pipeline_result.all_node_events] == [
        DagsterEventType.STEP_START.value,
        DagsterEventType.STEP_OUTPUT.value,
        DagsterEventType.STEP_FAILURE.value,
    ]
    for event in pipeline_result.all_node_events:
        if event.event_type_value == DagsterEventType.STEP_FAILURE.value:
            assert event.event_specific_data.error.cls_name == "DagsterTypeCheckDidNotPass"


def test_raise_on_error_true_type_check_returns_unsuccessful_type_check():
    FalsyType = DagsterType(
        name="FalsyType",
        type_check_fn=lambda _, _val: TypeCheck(
            success=False, metadata_entries=[MetadataEntry("bar", value="foo")]
        ),
    )

    @op(out=Out(FalsyType))
    def foo_op(_):
        return 1

    @job
    def foo_job():
        foo_op()

    with pytest.raises(DagsterTypeCheckDidNotPass) as e:
        foo_job.execute_in_process()
    assert e.value.metadata_entries[0].label == "bar"
    assert e.value.metadata_entries[0].entry_data.text == "foo"
    assert isinstance(e.value.dagster_type, DagsterType)

    pipeline_result = foo_job.execute_in_process(raise_on_error=False)
    assert not pipeline_result.success
    assert [event.event_type_value for event in pipeline_result.all_node_events] == [
        DagsterEventType.STEP_START.value,
        DagsterEventType.STEP_OUTPUT.value,
        DagsterEventType.STEP_FAILURE.value,
    ]
    for event in pipeline_result.all_node_events:
        if event.event_type_value == DagsterEventType.STEP_FAILURE.value:
            assert event.event_specific_data.error.cls_name == "DagsterTypeCheckDidNotPass"


def test_raise_on_error_true_type_check_raises_exception():
    def raise_exception_inner(_context, _):
        raise Failure("I am dissapoint")

    ThrowExceptionType = DagsterType(name="ThrowExceptionType", type_check_fn=raise_exception_inner)

    @op(out=Out(ThrowExceptionType))
    def foo_op(_):
        return 1

    @job
    def foo_job():
        foo_op()

    with pytest.raises(Failure, match=re.escape("I am dissapoint")):
        foo_job.execute_in_process()

    pipeline_result = foo_job.execute_in_process(raise_on_error=False)
    assert not pipeline_result.success
    assert [event.event_type_value for event in pipeline_result.all_node_events] == [
        DagsterEventType.STEP_START.value,
        DagsterEventType.STEP_FAILURE.value,
    ]
    for event in pipeline_result.all_node_events:
        if event.event_type_value == DagsterEventType.STEP_FAILURE.value:
            assert event.event_specific_data.error.cause.cls_name == "Failure"


def test_raise_on_error_true_type_check_returns_true():
    TruthyExceptionType = DagsterType(
        name="TruthyExceptionType", type_check_fn=lambda _, _val: True
    )

    @op(out=Out(TruthyExceptionType))
    def foo_op(_):
        return 1

    @job
    def foo_job():
        foo_op()

    assert foo_job.execute_in_process().success

    pipeline_result = foo_job.execute_in_process(raise_on_error=False)
    assert pipeline_result.success
    assert set(
        [
            DagsterEventType.STEP_START.value,
            DagsterEventType.STEP_OUTPUT.value,
            DagsterEventType.STEP_SUCCESS.value,
        ]
    ).issubset([event.event_type_value for event in pipeline_result.all_node_events])


def test_raise_on_error_true_type_check_returns_successful_type_check():
    TruthyExceptionType = DagsterType(
        name="TruthyExceptionType",
        type_check_fn=lambda _, _val: TypeCheck(
            success=True, metadata_entries=[MetadataEntry("bar", value="foo")]
        ),
    )

    @op(out=Out(TruthyExceptionType))
    def foo_op(_):
        return 1

    @job
    def foo_job():
        foo_op()

    pipeline_result = foo_job.execute_in_process()
    assert pipeline_result.success
    for event in pipeline_result.all_node_events:
        if event.event_type_value == DagsterEventType.STEP_OUTPUT.value:
            assert event.event_specific_data.type_check_data
            assert event.event_specific_data.type_check_data.metadata_entries[0].label == "bar"
            assert (
                event.event_specific_data.type_check_data.metadata_entries[0].entry_data.text
                == "foo"
            )
            assert event.event_specific_data.type_check_data.metadata_entries[0]

    pipeline_result = foo_job.execute_in_process(raise_on_error=False)
    assert pipeline_result.success
    assert set(
        [
            DagsterEventType.STEP_START.value,
            DagsterEventType.STEP_OUTPUT.value,
            DagsterEventType.STEP_SUCCESS.value,
        ]
    ).issubset([event.event_type_value for event in pipeline_result.all_node_events])


def test_contextual_type_check():
    def fancy_type_check(context, value):
        return TypeCheck(success=context.resources.foo.check(value))

    custom = DagsterType(
        key="custom",
        name="custom",
        type_check_fn=fancy_type_check,
        required_resource_keys={"foo"},
    )

    @resource
    def foo(_context):
        class _Foo:
            def check(self, _value):
                return True

        return _Foo()

    @op
    def return_one():
        return 1

    @op(ins={"inp": In(custom)})
    def bar(_context, inp):
        return inp

    @job(resource_defs={"foo": foo})
    def fancy_job():
        bar(return_one())

    assert fancy_job.execute_in_process().success


def test_type_equality():
    assert resolve_dagster_type(int) == resolve_dagster_type(int)
    assert not (resolve_dagster_type(int) != resolve_dagster_type(int))

    assert resolve_dagster_type(List[int]) == resolve_dagster_type(List[int])
    assert not (resolve_dagster_type(List[int]) != resolve_dagster_type(List[int]))

    assert resolve_dagster_type(Optional[List[int]]) == resolve_dagster_type(Optional[List[int]])
    assert not (
        resolve_dagster_type(Optional[List[int]]) != resolve_dagster_type(Optional[List[int]])
    )


def test_make_usable_as_dagster_type_called_twice():
    class AType:
        pass

    ADagsterType = PythonObjectDagsterType(
        AType,
        name="ADagsterType",
    )
    BDagsterType = PythonObjectDagsterType(
        AType,
        name="BDagsterType",
    )

    make_python_type_usable_as_dagster_type(AType, ADagsterType)
    make_python_type_usable_as_dagster_type(AType, ADagsterType)  # should not raise an error

    with pytest.raises(DagsterInvalidDefinitionError):
        make_python_type_usable_as_dagster_type(AType, BDagsterType)


def test_tuple_inner_types_not_mutable():
    tuple_type = Tuple[List[String]]
    inner_types_1st_call = list(tuple_type.inner_types)
    inner_types = list(tuple_type.inner_types)
    assert inner_types_1st_call == inner_types, "inner types mutated on subsequent calls"

    assert isinstance(inner_types[0], ListType)
    assert inner_types[0].inner_type == inner_types[1]
    assert len(inner_types) == 2
