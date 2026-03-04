import re
import typing

import dagster as dg
import pytest
from dagster import DagsterEventType
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.types.dagster_type import ListType, resolve_dagster_type


class BarObj:
    pass


class _Bar(dg.PythonObjectDagsterType):
    def __init__(self):
        super().__init__(BarObj, name="Bar", description="A bar.")


Bar = _Bar()


def test_python_object_type():
    type_bar = Bar

    assert type_bar.unique_name == "Bar"
    assert type_bar.description == "A bar."
    assert_success(type_bar, BarObj())

    assert_failure(type_bar, None)

    assert_failure(type_bar, "not_a_bar")


def test_python_object_union_type():
    ntype = dg.PythonObjectDagsterType(python_type=(int, float))
    assert ntype.unique_name == "Union[int, float]"
    assert_success(ntype, 1)
    assert_success(ntype, 1.5)
    assert_failure(ntype, "a")


def test_python_object_type_with_custom_type_check():
    def eq_3(_, value):
        return isinstance(value, int) and value == 3

    Int3 = dg.DagsterType(name="Int3", type_check_fn=eq_3)

    assert Int3.unique_name == "Int3"
    assert dg.check_dagster_type(Int3, 3).success
    assert not dg.check_dagster_type(Int3, 5).success


def test_tuple_union_typing_type():
    UnionType = dg.PythonObjectDagsterType(python_type=(str, int, float))

    assert UnionType.typing_type == typing.Union[str, int, float]  # noqa: UP007


def test_nullable_python_object_type():
    assert dg.check_dagster_type(dg.Optional[Bar], BarObj()).success
    assert dg.check_dagster_type(dg.Optional[Bar], None).success
    assert not dg.check_dagster_type(dg.Optional[Bar], "not_a_bar").success


def test_nullable_int_coercion():
    assert dg.check_dagster_type(dg.Int, 1).success
    assert not dg.check_dagster_type(dg.Int, None).success

    assert dg.check_dagster_type(dg.Optional[dg.Int], 1).success
    assert dg.check_dagster_type(dg.Optional[dg.Int], None).success


def assert_type_check(type_check):
    assert isinstance(type_check, dg.TypeCheck) and type_check.success


def assert_success(dagster_type, value):
    type_check_result = dagster_type.type_check(None, value)
    assert_type_check(type_check_result)


def assert_failure(dagster_type, value):
    res = dagster_type.type_check(None, value)
    assert not res.success


def test_nullable_list_combos_coerciion():
    assert not dg.check_dagster_type(dg.List[dg.Int], None).success
    assert dg.check_dagster_type(dg.List[dg.Int], []).success
    assert dg.check_dagster_type(dg.List[dg.Int], [1]).success
    assert not dg.check_dagster_type(dg.List[dg.Int], [None]).success

    assert dg.check_dagster_type(dg.Optional[dg.List[dg.Int]], None).success
    assert dg.check_dagster_type(dg.Optional[dg.List[dg.Int]], []).success
    assert dg.check_dagster_type(dg.Optional[dg.List[dg.Int]], [1]).success
    assert not dg.check_dagster_type(dg.Optional[dg.List[dg.Int]], [None]).success

    assert not dg.check_dagster_type(dg.List[dg.Optional[dg.Int]], None).success
    assert dg.check_dagster_type(dg.List[dg.Optional[dg.Int]], []).success
    assert dg.check_dagster_type(dg.List[dg.Optional[dg.Int]], [1]).success
    assert dg.check_dagster_type(dg.List[dg.Optional[dg.Int]], [None]).success

    assert dg.check_dagster_type(dg.Optional[dg.List[dg.Optional[dg.Int]]], None).success
    assert dg.check_dagster_type(dg.Optional[dg.List[dg.Optional[dg.Int]]], []).success
    assert dg.check_dagster_type(dg.Optional[dg.List[dg.Optional[dg.Int]]], [1]).success
    assert dg.check_dagster_type(dg.Optional[dg.List[dg.Optional[dg.Int]]], [None]).success


def execute_no_throw(job_def):
    return job_def.execute_in_process(raise_on_error=False)


def _type_check_data_for_input(result, op_name, input_name):
    events_for_op = result.events_for_node(op_name)
    step_input_event = next(
        event
        for event in events_for_op
        if event.event_type == DagsterEventType.STEP_INPUT
        and event.step_handle.to_key() == op_name
        and event.event_specific_data.input_name == input_name
    )
    return step_input_event.event_specific_data.type_check_data


def test_input_types_succeed_in_job():
    @dg.op
    def return_one():
        return 1

    @dg.op(ins={"num": dg.In(int)})
    def take_num(num):
        return num

    @dg.job
    def pipe():
        take_num(return_one())

    result = pipe.execute_in_process()
    assert result.success

    type_check_data = _type_check_data_for_input(result, op_name="take_num", input_name="num")
    assert type_check_data.success


def test_output_types_succeed_in_job():
    @dg.op(out=dg.Out(int))
    def return_one():
        return 1

    @dg.job
    def pipe():
        return_one()

    result = pipe.execute_in_process()
    assert result.success

    events_for_node = result.events_for_node("return_one")
    output_event = [
        event for event in events_for_node if event.event_type == DagsterEventType.STEP_OUTPUT
    ].pop()

    type_check_data = output_event.event_specific_data.type_check_data  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    assert type_check_data.success  # pyright: ignore[reportOptionalMemberAccess]


def test_input_types_fail_in_job():
    @dg.op
    def return_one():
        return 1

    @dg.op(ins={"string": dg.In(str)})
    def take_string(string):
        return string

    @dg.job
    def pipe():
        take_string(return_one())

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        pipe.execute_in_process()

    # now check events in no throw case

    result = execute_no_throw(pipe)

    assert not result.success

    type_check_data = _type_check_data_for_input(result, op_name="take_string", input_name="string")
    assert not type_check_data.success
    assert type_check_data.description == 'Value "1" of python type "int" must be a string.'

    failure_event = [
        event
        for event in result.events_for_node("take_string")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()
    assert failure_event.step_failure_data.error.cls_name == "DagsterTypeCheckDidNotPass"  # pyright: ignore[reportOptionalMemberAccess]


def test_output_types_fail_in_job():
    @dg.op(out=dg.Out(str))
    def return_int_fails():
        return 1

    @dg.job
    def pipe():
        return_int_fails()

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        pipe.execute_in_process()

    result = execute_no_throw(pipe)

    assert not result.success

    events_for_node = result.events_for_node("return_int_fails")
    output_event = [
        event for event in events_for_node if event.event_type == DagsterEventType.STEP_OUTPUT
    ].pop()

    type_check_data = output_event.event_specific_data.type_check_data  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    assert not type_check_data.success  # pyright: ignore[reportOptionalMemberAccess]
    assert type_check_data.description == 'Value "1" of python type "int" must be a string.'  # pyright: ignore[reportOptionalMemberAccess]

    failure_event = [
        event
        for event in result.events_for_node("return_int_fails")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()

    assert failure_event.step_failure_data.error.cls_name == "DagsterTypeCheckDidNotPass"  # pyright: ignore[reportOptionalMemberAccess]


# TODO add more step output use cases


class AlwaysFailsException(Exception):
    # Made to make exception explicit so that we aren't accidentally masking other Exceptions
    pass


def _always_fails(_, _value):
    raise AlwaysFailsException("kdjfkjd")


ThrowsExceptionType = dg.DagsterType(
    name="ThrowsExceptionType",
    type_check_fn=_always_fails,
)


def _return_bad_value(_, _value):
    return "foo"


BadType = dg.DagsterType(name="BadType", type_check_fn=_return_bad_value)  # pyright: ignore[reportArgumentType]


def test_input_type_returns_wrong_thing():
    @dg.op
    def return_one():
        return 1

    @dg.op(ins={"value": dg.In(BadType)})
    def take_bad_thing(value):
        return value

    @dg.job
    def pipe():
        take_bad_thing(return_one())

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=re.escape("You have returned 'foo' of type <")
        + "(class|type)"
        + re.escape(
            " 'str'> from the type check function of type \"BadType\". Return value must be"
            " instance of TypeCheck or a bool."
        ),
    ):
        pipe.execute_in_process()

    result = execute_no_throw(pipe)
    assert not result.success

    failure_event = [
        event
        for event in result.events_for_node("take_bad_thing")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()

    assert failure_event.step_failure_data.error.cls_name == "DagsterInvariantViolationError"  # pyright: ignore[reportOptionalMemberAccess]


def test_output_type_returns_wrong_thing():
    @dg.op(out=dg.Out(BadType))
    def return_one_bad_thing():
        return 1

    @dg.job
    def pipe():
        return_one_bad_thing()

    with pytest.raises(dg.DagsterInvariantViolationError):
        pipe.execute_in_process()

    result = execute_no_throw(pipe)
    assert not result.success

    failure_event = [
        event
        for event in result.events_for_node("return_one_bad_thing")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()
    assert failure_event.step_failure_data.error.cls_name == "DagsterInvariantViolationError"  # pyright: ignore[reportOptionalMemberAccess]


def test_input_type_throw_arbitrary_exception():
    @dg.op
    def return_one():
        return 1

    @dg.op(ins={"value": dg.In(ThrowsExceptionType)})
    def take_throws(value):
        return value

    @dg.job
    def pipe():
        take_throws(return_one())

    with pytest.raises(AlwaysFailsException):
        pipe.execute_in_process()

    result = execute_no_throw(pipe)
    assert not result.success
    failure_event = [
        event
        for event in result.events_for_node("take_throws")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()
    assert failure_event.step_failure_data.error.cause.cls_name == "AlwaysFailsException"  # pyright: ignore[reportOptionalMemberAccess]


def test_output_type_throw_arbitrary_exception():
    @dg.op(out=dg.Out(ThrowsExceptionType))
    def return_one_throws():
        return 1

    @dg.job
    def pipe():
        return_one_throws()

    with pytest.raises(AlwaysFailsException):
        pipe.execute_in_process()

    result = execute_no_throw(pipe)
    assert not result.success
    failure_event = [
        event
        for event in result.events_for_node("return_one_throws")
        if event.event_type == DagsterEventType.STEP_FAILURE
    ].pop()
    assert failure_event.step_failure_data.error.cause.cls_name == "AlwaysFailsException"  # pyright: ignore[reportOptionalMemberAccess]
    assert "kdjfkjd" in failure_event.step_failure_data.error.cause.message  # pyright: ignore[reportOptionalMemberAccess]


def define_custom_dict(name, permitted_key_names):
    def type_check_method(_, value):
        if not isinstance(value, dict):
            return dg.TypeCheck(
                False,
                description=f"Value {value} should be of type {name}.",
            )
        for key in value:
            if key not in permitted_key_names:
                return dg.TypeCheck(
                    False,
                    description=(
                        f"Key {value.name} is not a permitted value, values can only be of: {permitted_key_names}"  # pyright: ignore[reportAttributeAccessIssue]
                    ),
                )
        return dg.TypeCheck(
            True,
            metadata={
                "row_count": MetadataValue.text(str(len(value))),
                "series_names": MetadataValue.text(", ".join(value.keys())),
            },
        )

    return dg.DagsterType(key=name, name=name, type_check_fn=type_check_method)


def test_fan_in_custom_types_with_storage():
    CustomDict = define_custom_dict("CustomDict", ["foo", "bar"])

    @dg.op(out=dg.Out(CustomDict))
    def return_dict_1(_context):
        return {"foo": 3}

    @dg.op(out=dg.Out(CustomDict))
    def return_dict_2(_context):
        return {"bar": "zip"}

    @dg.op(ins={"dicts": dg.In(dg.List[CustomDict])})
    def get_foo(_context, dicts):
        return dicts[0]["foo"]

    @dg.job(resource_defs={"io_manager": dg.fs_io_manager})
    def dict_job():
        # Fan-in
        get_foo([return_dict_1(), return_dict_2()])

    result = dict_job.execute_in_process()
    assert result.success


ReturnBoolType = dg.DagsterType(name="ReturnBoolType", type_check_fn=lambda _, _val: True)


def test_return_bool_type():
    @dg.op(out=dg.Out(ReturnBoolType))
    def return_always_pass_bool_type(_):
        return 1

    @dg.job
    def bool_type_job():
        return_always_pass_bool_type()

    assert bool_type_job.execute_in_process().success


def test_raise_on_error_type_check_returns_false():
    FalsyType = dg.DagsterType(name="FalsyType", type_check_fn=lambda _, _val: False)

    @dg.op(out=dg.Out(FalsyType))
    def foo_op(_):
        return 1

    @dg.job
    def foo_job():
        foo_op()

    with pytest.raises(dg.DagsterTypeCheckDidNotPass):
        foo_job.execute_in_process()

    result = foo_job.execute_in_process(raise_on_error=False)
    assert not result.success
    assert [event.event_type_value for event in result.all_node_events] == [
        DagsterEventType.STEP_START.value,
        DagsterEventType.STEP_OUTPUT.value,
        DagsterEventType.STEP_FAILURE.value,
    ]
    for event in result.all_node_events:
        if event.event_type_value == DagsterEventType.STEP_FAILURE.value:
            assert event.event_specific_data.error.cls_name == "DagsterTypeCheckDidNotPass"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_raise_on_error_true_type_check_returns_unsuccessful_type_check():
    FalsyType = dg.DagsterType(
        name="FalsyType",
        type_check_fn=lambda _, _val: dg.TypeCheck(success=False, metadata={"bar": "foo"}),
    )

    @dg.op(out=dg.Out(FalsyType))
    def foo_op(_):
        return 1

    @dg.job
    def foo_job():
        foo_op()

    with pytest.raises(dg.DagsterTypeCheckDidNotPass) as e:
        foo_job.execute_in_process()
    assert "bar" in e.value.metadata
    assert e.value.metadata["bar"].text == "foo"
    assert isinstance(e.value.dagster_type, dg.DagsterType)

    result = foo_job.execute_in_process(raise_on_error=False)
    assert not result.success
    assert [event.event_type_value for event in result.all_node_events] == [
        DagsterEventType.STEP_START.value,
        DagsterEventType.STEP_OUTPUT.value,
        DagsterEventType.STEP_FAILURE.value,
    ]
    for event in result.all_node_events:
        if event.event_type_value == DagsterEventType.STEP_FAILURE.value:
            assert event.event_specific_data.error.cls_name == "DagsterTypeCheckDidNotPass"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_raise_on_error_true_type_check_raises_exception():
    def raise_exception_inner(_context, _):
        raise dg.Failure("I am dissapoint")

    ThrowExceptionType = dg.DagsterType(
        name="ThrowExceptionType", type_check_fn=raise_exception_inner
    )

    @dg.op(out=dg.Out(ThrowExceptionType))
    def foo_op(_):
        return 1

    @dg.job
    def foo_job():
        foo_op()

    with pytest.raises(dg.Failure, match=re.escape("I am dissapoint")):
        foo_job.execute_in_process()

    result = foo_job.execute_in_process(raise_on_error=False)
    assert not result.success
    assert [event.event_type_value for event in result.all_node_events] == [
        DagsterEventType.STEP_START.value,
        DagsterEventType.STEP_FAILURE.value,
    ]
    for event in result.all_node_events:
        if event.event_type_value == DagsterEventType.STEP_FAILURE.value:
            assert event.event_specific_data.error.cause.cls_name == "Failure"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]


def test_raise_on_error_true_type_check_returns_true():
    TruthyExceptionType = dg.DagsterType(
        name="TruthyExceptionType", type_check_fn=lambda _, _val: True
    )

    @dg.op(out=dg.Out(TruthyExceptionType))
    def foo_op(_):
        return 1

    @dg.job
    def foo_job():
        foo_op()

    assert foo_job.execute_in_process().success

    result = foo_job.execute_in_process(raise_on_error=False)
    assert result.success
    assert set(
        [
            DagsterEventType.STEP_START.value,
            DagsterEventType.STEP_OUTPUT.value,
            DagsterEventType.STEP_SUCCESS.value,
        ]
    ).issubset([event.event_type_value for event in result.all_node_events])


def test_raise_on_error_true_type_check_returns_successful_type_check():
    TruthyExceptionType = dg.DagsterType(
        name="TruthyExceptionType",
        type_check_fn=lambda _, _val: dg.TypeCheck(success=True, metadata={"bar": "foo"}),
    )

    @dg.op(out=dg.Out(TruthyExceptionType))
    def foo_op(_):
        return 1

    @dg.job
    def foo_job():
        foo_op()

    result = foo_job.execute_in_process()
    assert result.success
    for event in result.all_node_events:
        if event.event_type_value == DagsterEventType.STEP_OUTPUT.value:
            assert event.event_specific_data.type_check_data  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
            assert event.event_specific_data.type_check_data.metadata["bar"].text == "foo"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]

    result = foo_job.execute_in_process(raise_on_error=False)
    assert result.success
    assert set(
        [
            DagsterEventType.STEP_START.value,
            DagsterEventType.STEP_OUTPUT.value,
            DagsterEventType.STEP_SUCCESS.value,
        ]
    ).issubset([event.event_type_value for event in result.all_node_events])


def test_contextual_type_check():
    def fancy_type_check(context, value):
        return dg.TypeCheck(success=context.resources.foo.check(value))

    custom = dg.DagsterType(
        key="custom",
        name="custom",
        type_check_fn=fancy_type_check,
        required_resource_keys={"foo"},
    )

    @dg.resource
    def foo(_context):
        class _Foo:
            def check(self, _value):
                return True

        return _Foo()

    @dg.op
    def return_one():
        return 1

    @dg.op(ins={"inp": dg.In(custom)})
    def bar(_context, inp):
        return inp

    @dg.job(resource_defs={"foo": foo})
    def fancy_job():
        bar(return_one())

    assert fancy_job.execute_in_process().success


def test_type_equality():
    assert resolve_dagster_type(int) == resolve_dagster_type(int)
    assert not (resolve_dagster_type(int) != resolve_dagster_type(int))

    assert resolve_dagster_type(dg.List[int]) == resolve_dagster_type(dg.List[int])
    assert not (resolve_dagster_type(dg.List[int]) != resolve_dagster_type(dg.List[int]))

    assert resolve_dagster_type(dg.Optional[dg.List[int]]) == resolve_dagster_type(
        dg.Optional[dg.List[int]]
    )
    assert not (
        resolve_dagster_type(dg.Optional[dg.List[int]])
        != resolve_dagster_type(dg.Optional[dg.List[int]])
    )


def test_make_usable_as_dagster_type_called_twice():
    class AType:
        pass

    ADagsterType = dg.PythonObjectDagsterType(
        AType,
        name="ADagsterType",
    )
    BDagsterType = dg.PythonObjectDagsterType(
        AType,
        name="BDagsterType",
    )

    dg.make_python_type_usable_as_dagster_type(AType, ADagsterType)
    dg.make_python_type_usable_as_dagster_type(AType, ADagsterType)  # should not raise an error

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        dg.make_python_type_usable_as_dagster_type(AType, BDagsterType)


def test_tuple_inner_types_not_mutable():
    tuple_type = dg.Tuple[dg.List[dg.String]]
    inner_types_1st_call = list(tuple_type.inner_types)
    inner_types = list(tuple_type.inner_types)
    assert inner_types_1st_call == inner_types, "inner types mutated on subsequent calls"

    assert isinstance(inner_types[0], ListType)
    assert inner_types[0].inner_type == inner_types[1]
    assert len(inner_types) == 2
