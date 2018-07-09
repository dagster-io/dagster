from six import (string_types, integer_types)

from dagster import check


class DagsterType:
    def is_python_valid_value(self, _value):
        check.not_implemented('Must implement in subclass')


class _SolidStringType(DagsterType):
    def __init__(self, name):
        self.name = check.str_param(name, 'name')

    def is_python_valid_value(self, value):
        return isinstance(value, string_types)


class _SolidIntType(DagsterType):
    def __init__(self):
        self.name = 'INT'

    def is_python_valid_value(self, value):
        return isinstance(value, integer_types)


STRING = _SolidStringType(name='String')
PATH = _SolidStringType(name='Path')
INT = _SolidIntType()
