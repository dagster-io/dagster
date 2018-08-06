from dagster.core.types import (DagsterType, PythonObjectType)


def test_desc():
    type_foo = DagsterType(name='Foo', description='A foo')
    assert type_foo.name == 'Foo'
    assert type_foo.description == 'A foo'


def test_python_object_type():
    class Bar:
        pass

    type_bar = PythonObjectType('Bar', Bar, description='A bar.')

    assert type_bar.name == 'Bar'
    assert type_bar.description == 'A bar.'
    assert type_bar.is_python_valid_value(Bar())
    assert type_bar.is_python_valid_value(None)  # allow nulls
    assert not type_bar.is_python_valid_value('not_a_bar')
