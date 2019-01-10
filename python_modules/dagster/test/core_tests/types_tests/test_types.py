import pytest

from dagster.core.errors import DagsterRuntimeCoercionError

from dagster.core.types import Int, Nullable, List, PythonObjectType
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
    assert type_bar.coerce_runtime_value(BarObj())

    with pytest.raises(DagsterRuntimeCoercionError):
        assert type_bar.coerce_runtime_value(None)
    with pytest.raises(DagsterRuntimeCoercionError):
        type_bar.coerce_runtime_value('not_a_bar')


def test_nullable_python_object_type():
    nullable_type_bar = resolve_to_runtime_type(Nullable(Bar))

    assert nullable_type_bar.coerce_runtime_value(BarObj())
    assert nullable_type_bar.coerce_runtime_value(None) is None

    with pytest.raises(DagsterRuntimeCoercionError):
        nullable_type_bar.coerce_runtime_value('not_a_bar')


def test_nullable_int_coercion():
    int_type = resolve_to_runtime_type(Int)
    assert int_type.coerce_runtime_value(1) == 1

    with pytest.raises(DagsterRuntimeCoercionError):
        assert int_type.coerce_runtime_value(None)

    nullable_int_type = resolve_to_runtime_type(Nullable(Int))
    assert nullable_int_type.coerce_runtime_value(1) == 1
    assert nullable_int_type.coerce_runtime_value(None) is None


def assert_success(fn, value):
    assert fn(value) == value


def assert_failure(fn, value):
    with pytest.raises(DagsterRuntimeCoercionError):
        fn(value)


def test_nullable_list_combos_coerciion():

    list_of_int = resolve_to_runtime_type(List(Int))

    assert_failure(list_of_int.coerce_runtime_value, None)
    assert_success(list_of_int.coerce_runtime_value, [])
    assert_success(list_of_int.coerce_runtime_value, [1])
    assert_failure(list_of_int.coerce_runtime_value, [None])

    nullable_int_of_list = resolve_to_runtime_type(Nullable(List(Int)))

    assert_success(nullable_int_of_list.coerce_runtime_value, None)
    assert_success(nullable_int_of_list.coerce_runtime_value, [])
    assert_success(nullable_int_of_list.coerce_runtime_value, [1])
    assert_failure(nullable_int_of_list.coerce_runtime_value, [None])

    list_of_nullable_int = resolve_to_runtime_type(List(Nullable(Int)))
    assert_failure(list_of_nullable_int.coerce_runtime_value, None)
    assert_success(list_of_nullable_int.coerce_runtime_value, [])
    assert_success(list_of_nullable_int.coerce_runtime_value, [1])
    assert_success(list_of_nullable_int.coerce_runtime_value, [None])

    nullable_list_of_nullable_int = resolve_to_runtime_type(Nullable(List(Nullable(Int))))
    assert_success(nullable_list_of_nullable_int.coerce_runtime_value, None)
    assert_success(nullable_list_of_nullable_int.coerce_runtime_value, [])
    assert_success(nullable_list_of_nullable_int.coerce_runtime_value, [1])
    assert_success(nullable_list_of_nullable_int.coerce_runtime_value, [None])
