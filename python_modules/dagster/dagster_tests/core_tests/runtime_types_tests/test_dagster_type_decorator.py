import collections

import pytest

from dagster import DagsterInvalidDefinitionError, as_dagster_type, dagster_type
from dagster.core.types.runtime import RuntimeType, resolve_to_runtime_type


def test_dagster_type_decorator():
    @dagster_type(name=None)
    class Foo(object):
        pass

    @dagster_type()
    class Bar(object):
        pass

    @dagster_type
    class Baaz(object):
        pass

    assert resolve_to_runtime_type(Foo).name == 'Foo'
    assert resolve_to_runtime_type(Bar).name == 'Bar'
    assert resolve_to_runtime_type(Baaz).name == 'Baaz'


def test_dagster_type_decorator_name_desc():
    @dagster_type(name='DifferentName', description='desc')
    class Something(object):
        pass

    runtime_type = resolve_to_runtime_type(Something)
    assert runtime_type.name == 'DifferentName'
    assert runtime_type.description == 'desc'


def test_make_dagster_type():
    OverwriteNameTuple = as_dagster_type(collections.namedtuple('SomeNamedTuple', 'prop'))
    runtime_type = resolve_to_runtime_type(OverwriteNameTuple)
    assert runtime_type.name == 'SomeNamedTuple'
    assert OverwriteNameTuple(prop='foo').prop == 'foo'

    OverwriteNameTuple = as_dagster_type(
        collections.namedtuple('SomeNamedTuple', 'prop'), name='OverwriteName'
    )
    runtime_type = resolve_to_runtime_type(OverwriteNameTuple)
    assert runtime_type.name == 'OverwriteName'
    assert OverwriteNameTuple(prop='foo').prop == 'foo'


def test_make_dagster_type_from_builtin():
    OrderedDict = as_dagster_type(collections.OrderedDict)
    assert OrderedDict is collections.OrderedDict
    assert OrderedDict([('foo', 'bar')]) == collections.OrderedDict([('foo', 'bar')])
    assert isinstance(resolve_to_runtime_type(OrderedDict), RuntimeType)
    assert resolve_to_runtime_type(OrderedDict).python_type is collections.OrderedDict


def test_dagster_type_collision():
    class Foo(object):
        pass

    _Foo_1 = as_dagster_type(Foo)
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='A Dagster runtime type has already been registered for the Python type',
    ):
        _Foo_2 = as_dagster_type(Foo)
