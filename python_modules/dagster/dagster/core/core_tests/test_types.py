from collections import namedtuple
import pytest
from dagster.core.types import (
    DagsterCompositeType,
    DagsterEvaluateValueError,
    DagsterType,
    Field,
    Int,
    PythonObjectType,
    String,
)


def test_desc():
    type_foo = DagsterType(name='Foo', description='A foo')
    assert type_foo.name == 'Foo'
    assert type_foo.description == 'A foo'


def test_python_object_type():
    class Bar(object):
        pass

    type_bar = PythonObjectType('Bar', Bar, description='A bar.')

    assert type_bar.name == 'Bar'
    assert type_bar.description == 'A bar.'
    assert type_bar.evaluate_value(Bar())
    assert type_bar.evaluate_value(None) is None  # allow nulls
    with pytest.raises(DagsterEvaluateValueError):
        type_bar.evaluate_value('not_a_bar')
