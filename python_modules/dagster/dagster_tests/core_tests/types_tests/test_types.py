import pytest

from dagster import (
    DagsterInvariantViolationError,
    DagsterTypeCheckError,
    Failure,
    InputDefinition,
    OutputDefinition,
    RuntimeType,
    TypeCheck,
    execute_pipeline,
    lambda_solid,
    pipeline,
)

from dagster.core.types import Int, Optional, List, PythonObjectType
from dagster.core.types.runtime import resolve_to_runtime_type


class BarObj(object):
    pass


class Bar(PythonObjectType):
    def __init__(self):
        super(Bar, self).__init__(BarObj, description='A bar.')


def test_python_object_type():
    type_bar = Bar.inst()

    assert type_bar.name == 'Bar'
    assert type_bar.description == 'A bar.'
    assert_type_check(type_bar.type_check(BarObj()))

    with pytest.raises(Failure):
        assert type_bar.type_check(None)

    with pytest.raises(Failure):
        type_bar.type_check('not_a_bar')


def test_nullable_python_object_type():
    nullable_type_bar = resolve_to_runtime_type(Optional[Bar])

    assert_type_check(nullable_type_bar.type_check(BarObj()))
    assert_type_check(nullable_type_bar.type_check(None))

    with pytest.raises(Failure):
        nullable_type_bar.type_check('not_a_bar')


def test_nullable_int_coercion():
    int_type = resolve_to_runtime_type(Int)
    assert_type_check(int_type.type_check(1))

    with pytest.raises(Failure):
        int_type.type_check(None)

    nullable_int_type = resolve_to_runtime_type(Optional[Int])
    assert_type_check(nullable_int_type.type_check(1))
    assert_type_check(nullable_int_type.type_check(None))


def assert_type_check(type_check):
    assert type_check is None or isinstance(type_check, TypeCheck)


def assert_success(runtime_type, value):
    type_check_result = runtime_type.type_check(value)
    assert_type_check(type_check_result)


def assert_failure(runtime_type, value):
    with pytest.raises(Failure):
        runtime_type.type_check(value)


def test_nullable_list_combos_coerciion():

    list_of_int = resolve_to_runtime_type(List[Int])

    assert_failure(list_of_int, None)
    assert_success(list_of_int, [])
    assert_success(list_of_int, [1])
    assert_failure(list_of_int, [None])

    nullable_int_of_list = resolve_to_runtime_type(Optional[List[Int]])

    assert_success(nullable_int_of_list, None)
    assert_success(nullable_int_of_list, [])
    assert_success(nullable_int_of_list, [1])
    assert_failure(nullable_int_of_list, [None])

    list_of_nullable_int = resolve_to_runtime_type(List[Optional[Int]])
    assert_failure(list_of_nullable_int, None)
    assert_success(list_of_nullable_int, [])
    assert_success(list_of_nullable_int, [1])
    assert_success(list_of_nullable_int, [None])

    nullable_list_of_nullable_int = resolve_to_runtime_type(Optional[List[Optional[Int]]])
    assert_success(nullable_list_of_nullable_int, None)
    assert_success(nullable_list_of_nullable_int, [])
    assert_success(nullable_list_of_nullable_int, [1])
    assert_success(nullable_list_of_nullable_int, [None])


def test_input_types_in_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(inputs=[InputDefinition('string', str)])
    def take_string(string):
        return string

    @pipeline
    def pipe():
        return take_string(return_one())

    with pytest.raises(DagsterTypeCheckError) as exc_info:
        execute_pipeline(pipe)

    assert 'In solid "take_string" the input "string" received value 1 of Python ' in str(
        exc_info.value
    )


def test_output_types_in_pipeline():
    @lambda_solid(output=OutputDefinition(str))
    def return_int_fails():
        return 1

    @pipeline
    def pipe():
        return return_int_fails()

    with pytest.raises(DagsterTypeCheckError) as exc_info:
        execute_pipeline(pipe)

    assert 'In solid "return_int_fails" the output result receive value 1 ' in str(exc_info.value)


class BadType(RuntimeType):
    def __init__(self):
        super(BadType, self).__init__(key='BadType', name='BadType')

    def type_check(self, value):
        return 'kdjfkjd'


def test_input_type_returns_wrong_thing():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(inputs=[InputDefinition('value', BadType)])
    def take_bad_thing(value):
        return value

    @pipeline
    def pipe():
        return take_bad_thing(return_one())

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(pipe)


def test_output_type_returns_wrong_thing():
    @lambda_solid(output=OutputDefinition(BadType))
    def return_bad_type():
        return 1

    @pipeline
    def pipe():
        return return_bad_type()

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(pipe)
