from six import string_types

from dagster import check


class SolidType:
    def is_python_valid_value(self, _value):
        check.not_implemented('Must implement in subclass')


class SolidStringType(SolidType):
    def __init__(self, name):
        self.name = check.str_param(name, 'name')

    def is_python_valid_value(self, value):
        return isinstance(value, string_types)


SolidString = SolidStringType(name='String')
SolidPath = SolidStringType(name='Path')
