from collections import namedtuple
from dagster.core.types.decorator import (
    dagster_type,
    get_runtime_type_on_decorated_klass,
    as_dagster_type,
)


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

    assert get_runtime_type_on_decorated_klass(Foo).name == 'Foo'
    assert get_runtime_type_on_decorated_klass(Bar).name == 'Bar'
    assert get_runtime_type_on_decorated_klass(Baaz).name == 'Baaz'


def test_dagster_type_decorator_name_desc():
    @dagster_type(name='DifferentName', description='desc')
    class Something(object):
        pass

    runtime_type = get_runtime_type_on_decorated_klass(Something)
    assert runtime_type.name == 'DifferentName'
    assert runtime_type.description == 'desc'


def test_make_dagster_type():
    OverwriteNameTuple = as_dagster_type(namedtuple('SomeNamedTuple', 'prop'))
    runtime_type = get_runtime_type_on_decorated_klass(OverwriteNameTuple)
    assert runtime_type.name == 'SomeNamedTuple'
    assert OverwriteNameTuple(prop='foo').prop == 'foo'

    OverwriteNameTuple = as_dagster_type(namedtuple('SomeNamedTuple', 'prop'), name='OverwriteName')
    runtime_type = get_runtime_type_on_decorated_klass(OverwriteNameTuple)
    assert runtime_type.name == 'OverwriteName'
    assert OverwriteNameTuple(prop='foo').prop == 'foo'
