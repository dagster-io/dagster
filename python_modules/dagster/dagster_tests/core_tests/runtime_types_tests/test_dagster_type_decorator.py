import collections

from dagster import PythonObjectDagsterType, usable_as_dagster_type
from dagster.core.types.dagster_type import resolve_dagster_type


def test_dagster_type_decorator():
    @usable_as_dagster_type(name=None)
    class Foo(object):
        pass

    @usable_as_dagster_type()
    class Bar(object):
        pass

    @usable_as_dagster_type
    class Baaz(object):
        pass

    assert resolve_dagster_type(Foo).name == 'Foo'
    assert resolve_dagster_type(Bar).name == 'Bar'
    assert resolve_dagster_type(Baaz).name == 'Baaz'


def test_dagster_type_decorator_name_desc():
    @usable_as_dagster_type(name='DifferentName', description='desc')
    class Something(object):
        pass

    runtime_type = resolve_dagster_type(Something)
    assert runtime_type.name == 'DifferentName'
    assert runtime_type.description == 'desc'


def test_make_dagster_type():
    SomeNamedTuple = collections.namedtuple('SomeNamedTuple', 'prop')
    DagsterSomeNamedTuple = PythonObjectDagsterType(SomeNamedTuple)
    runtime_type = resolve_dagster_type(DagsterSomeNamedTuple)
    assert runtime_type.name == 'SomeNamedTuple'
    assert SomeNamedTuple(prop='foo').prop == 'foo'

    DagsterNewNameNamedTuple = PythonObjectDagsterType(SomeNamedTuple, name='OverwriteName')
    runtime_type = resolve_dagster_type(DagsterNewNameNamedTuple)
    assert runtime_type.name == 'OverwriteName'
