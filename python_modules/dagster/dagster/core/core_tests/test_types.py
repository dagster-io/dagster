import pytest

from dagster import types

from dagster.core.types import (
    DagsterRuntimeCoercionError,
    DagsterListType,
    DagsterType,
    PythonObjectType,
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
    assert type_bar.coerce_runtime_value(None) is None  # allow nulls
    assert type_bar.type_attributes.is_builtin is False
    assert type_bar.type_attributes.is_system_config is False
    with pytest.raises(DagsterRuntimeCoercionError):
        type_bar.coerce_runtime_value('not_a_bar')


def test_builtin_scalars():
    for builtin_scalar in [types.String, types.Int, types.Dict, types.Any, types.Bool, types.Path]:
        assert builtin_scalar.type_attributes.is_builtin is True
        assert builtin_scalar.type_attributes.is_system_config is False
