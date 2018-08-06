from six import (string_types, integer_types)

from dagster import check

import dagster


class DagsterType:
    def __init__(self, name, description=None):
        self.name = check.str_param(name, 'name')
        self.description = check.opt_str_param(description, 'description')

    def is_python_valid_value(self, _value):
        check.not_implemented('Must implement in subclass')


class DagsterScalarType(DagsterType):
    pass


class _DagsterAnyType(DagsterType):
    def __init__(self):
        super().__init__(
            name='Any', description='The type that allows any value, including no value.'
        )

    def is_python_valid_value(self, _value):
        return True


def _nullable_isinstance(value, typez):
    return value is None or isinstance(value, typez)


class PythonObjectType(DagsterType):
    def __init__(
        self,
        name,
        python_type,
        default_sources=None,
        default_materializations=None,
        description=None,
    ):
        super().__init__(name, description)
        self.python_type = check.type_param(python_type, 'python_type')
        self.default_sources = check.opt_list_param(
            default_sources, 'default_sources', of_type=dagster.SourceDefinition
        )
        self.default_materializations = check.opt_list_param(
            default_materializations,
            'default_materializations',
            of_type=dagster.MaterializationDefinition
        )

    def is_python_valid_value(self, value):
        return _nullable_isinstance(value, self.python_type)


class _DagsterStringType(DagsterScalarType):
    def is_python_valid_value(self, value):
        return _nullable_isinstance(value, string_types)


class _DagsterIntType(DagsterScalarType):
    def __init__(self):
        super().__init__('Int', description='An integer.')

    def is_python_valid_value(self, value):
        return _nullable_isinstance(value, integer_types)


class _DagsterBoolType(DagsterScalarType):
    def __init__(self):
        super().__init__('Bool', description='A boolean.')

    def is_python_valid_value(self, value):
        return _nullable_isinstance(value, bool)


String = _DagsterStringType(name='String', description='A string.')
Path = _DagsterStringType(
    name='Path',
    description='''
A string the represents a path. It is very useful for some tooling
to know that a string indeed represents a file path. That way they
can, for example, make the paths relative to a different location
for a particular execution environment.
''',
)
Int = _DagsterIntType()
Bool = _DagsterBoolType()
Any = _DagsterAnyType()
