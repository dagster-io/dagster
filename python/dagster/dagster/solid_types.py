from six import string_types

import check


class SolidType:
    def is_python_valid_value(self, _value):
        check.not_implemented('Must implement in subclass')


class SolidScalarType(SolidType):
    def __init__(self, name):
        self.name = check.str_param(name, 'name')

    def is_python_valid_value(self, value):
        return isinstance(value, string_types)


SolidString = SolidScalarType(name='String')
