from six import (string_types, integer_types)

from dagster import check


class DagsterType:
    def is_python_valid_value(self, _value):
        check.not_implemented('Must implement in subclass')


class _DagsterStringType(DagsterType):
    def __init__(self, name):
        self.name = check.str_param(name, 'name')

    def is_python_valid_value(self, value):
        return isinstance(value, string_types)


class _DagsterIntType(DagsterType):
    def __init__(self):
        self.name = 'Int'

    def is_python_valid_value(self, value):
        return isinstance(value, integer_types)


class _DagsterBoolType(DagsterType):
    def __init__(self):
        self.name = 'Bool'

    def is_python_valid_value(self, value):
        return isinstance(value, bool)


String = _DagsterStringType(name='String')
Path = _DagsterStringType(name='Path')
Int = _DagsterIntType()
Bool = _DagsterBoolType()
