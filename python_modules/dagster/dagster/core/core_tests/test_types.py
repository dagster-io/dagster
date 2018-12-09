import pytest

from dagster import types

from dagster.core.types import (
    DagsterRuntimeCoercionError,
    DagsterType,
    PythonObjectType,
    Nullable,
)


def test_desc():
    type_foo = DagsterType(name='Foo', description='A foo')
    assert type_foo.name == 'Foo'
    assert type_foo.description == 'A foo'
    assert type_foo.type_attributes.is_builtin is False
    assert type_foo.type_attributes.is_system_config is False


def test_python_object_type():
    class Bar(object):
        pass

    type_bar = PythonObjectType('Bar', Bar, description='A bar.')

    assert type_bar.name == 'Bar'
    assert type_bar.description == 'A bar.'
    assert type_bar.coerce_runtime_value(Bar())
    assert type_bar.type_attributes.is_builtin is False
    assert type_bar.type_attributes.is_system_config is False

    with pytest.raises(DagsterRuntimeCoercionError):
        assert type_bar.coerce_runtime_value(None)
    with pytest.raises(DagsterRuntimeCoercionError):
        type_bar.coerce_runtime_value('not_a_bar')


def test_builtin_scalars():
    for builtin_scalar in [types.String, types.Int, types.Any, types.Bool, types.Path]:
        assert builtin_scalar.type_attributes.is_builtin is True
        assert builtin_scalar.type_attributes.is_system_config is False


def test_nullable_python_object_type():
    class Bar(object):
        pass

    nullable_type_bar = Nullable(PythonObjectType('Bar', Bar, description='A bar.'))

    assert nullable_type_bar.coerce_runtime_value(Bar())
    assert nullable_type_bar.coerce_runtime_value(None) is None

    with pytest.raises(DagsterRuntimeCoercionError):
        nullable_type_bar.coerce_runtime_value('not_a_bar')


def test_nullable_int_coercion():
    assert types.Int.coerce_runtime_value(1) == 1

    with pytest.raises(DagsterRuntimeCoercionError):
        assert types.Int.coerce_runtime_value(None)

    assert types.Nullable(types.Int).coerce_runtime_value(1) == 1
    assert types.Nullable(types.Int).coerce_runtime_value(None) is None


def assert_success(fn, value):
    assert fn(value) == value


def assert_failure(fn, value):
    with pytest.raises(DagsterRuntimeCoercionError):
        fn(value)


def test_nullable_list_combos_coerciion():

    list_of_int = types.List(types.Int)

    assert_failure(list_of_int.coerce_runtime_value, None)
    assert_success(list_of_int.coerce_runtime_value, [])
    assert_success(list_of_int.coerce_runtime_value, [1])
    assert_failure(list_of_int.coerce_runtime_value, [None])

    nullable_int_of_list = types.Nullable(types.List(types.Int))

    assert_success(nullable_int_of_list.coerce_runtime_value, None)
    assert_success(nullable_int_of_list.coerce_runtime_value, [])
    assert_success(nullable_int_of_list.coerce_runtime_value, [1])
    assert_failure(nullable_int_of_list.coerce_runtime_value, [None])

    list_of_nullable_int = types.List(types.Nullable(types.Int))
    assert_failure(list_of_nullable_int.coerce_runtime_value, None)
    assert_success(list_of_nullable_int.coerce_runtime_value, [])
    assert_success(list_of_nullable_int.coerce_runtime_value, [1])
    assert_success(list_of_nullable_int.coerce_runtime_value, [None])

    nullable_list_of_nullable_int = types.Nullable(types.List(types.Nullable(types.Int)))
    assert_success(nullable_list_of_nullable_int.coerce_runtime_value, None)
    assert_success(nullable_list_of_nullable_int.coerce_runtime_value, [])
    assert_success(nullable_list_of_nullable_int.coerce_runtime_value, [1])
    assert_success(nullable_list_of_nullable_int.coerce_runtime_value, [None])