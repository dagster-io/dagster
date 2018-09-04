from collections import namedtuple
from six import (string_types, integer_types)

from dagster import check


class DagsterType(object):
    def __init__(self, name, description=None):
        self.name = check.str_param(name, 'name')
        self.description = check.opt_str_param(description, 'description')

    def __repr__(self):
        return 'DagsterType({name})'.format(name=self.name)

    def evaluate_value(self, _value):
        check.not_implemented('Must implement in subclass')


class DagsterScalarType(DagsterType):
    def __init__(self, *args, **kwargs):
        super(DagsterScalarType, self).__init__(*args, **kwargs)

    def process_value(self, value):
        return value

    def is_python_valid_value(self, _value):
        raise Exception('must implement')

    def evaluate_value(self, value):
        if not self.is_python_valid_value(value):
            return IncomingValueResult.create_failure(
                'Expected valid value for {type_name} but got {value}'.format(
                    type_name=self.name, value=repr(value)
                )
            )
        return IncomingValueResult.create_success(value)


class _DagsterAnyType(DagsterType):
    def __init__(self):
        super(_DagsterAnyType, self).__init__(
            name='Any', description='The type that allows any value, including no value.'
        )

    def is_python_valid_value(self, _value):
        return True

    def process_value(self, value):
        return value

    def evaluate_value(self, value):
        return IncomingValueResult.create_success(value)


def nullable_isinstance(value, typez):
    return value is None or isinstance(value, typez)


class PythonObjectType(DagsterType):
    def __init__(
        self,
        name,
        python_type,
        description=None,
    ):
        super(PythonObjectType, self).__init__(name, description)
        self.python_type = check.type_param(python_type, 'python_type')

    def is_python_valid_value(self, value):
        return nullable_isinstance(value, self.python_type)

    def evaluate_value(self, value):
        if not self.is_python_valid_value(value):
            return IncomingValueResult.create_failure(
                'Expected valid value for {type_name} but got {value}'.format(
                    type_name=self.name, value=repr(value)
                )
            )
        return IncomingValueResult.create_success(value)


class _DagsterStringType(DagsterScalarType):
    def is_python_valid_value(self, value):
        return nullable_isinstance(value, string_types)


class _DagsterIntType(DagsterScalarType):
    def __init__(self):
        super(_DagsterIntType, self).__init__('Int', description='An integer.')

    def is_python_valid_value(self, value):
        if isinstance(value, bool):
            return False
        return nullable_isinstance(value, integer_types)


class _DagsterBoolType(DagsterScalarType):
    def __init__(self):
        super(_DagsterBoolType, self).__init__('Bool', description='A boolean.')

    def is_python_valid_value(self, value):
        return nullable_isinstance(value, bool)


class __FieldValueSentinel:
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel


class Field:
    '''
    A Field in a DagsterCompositeType.

    Attributes:
        dagster_type (DagsterType): The type of the field.
        default_value (Any):
            If the Field is optional, a default value can be provided when the field value
            is not specified.
        is_optional (bool): Is the field optional.
        description (str): Description of the field.
    '''

    def __init__(
        self,
        dagster_type,
        default_value=FIELD_NO_DEFAULT_PROVIDED,
        is_optional=False,
        description=None
    ):
        if not is_optional:
            check.param_invariant(
                default_value == FIELD_NO_DEFAULT_PROVIDED,
                'default_value',
                'required arguments should not specify default values',
            )

        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)
        self.description = check.opt_str_param(description, 'description')
        self.is_optional = check.bool_param(is_optional, 'is_optional')
        self.default_value = default_value

    @property
    def default_provided(self):
        '''Was a default value provided

        Returns:
            bool: Yes or no
        '''
        return self.default_value != FIELD_NO_DEFAULT_PROVIDED


class FieldDefinitionDictionary(dict):
    def __init__(self, ddict):
        check.dict_param(ddict, 'ddict', key_type=str, value_type=Field)
        super(FieldDefinitionDictionary, self).__init__(ddict)

    def __setitem__(self, _key, _value):
        check.failed('This dictionary is readonly')


class DagsterCompositeType(DagsterType):
    def __init__(self, name, fields, ctor, description=None):
        self.field_dict = FieldDefinitionDictionary(fields)
        self.ctor = check.callable_param(ctor, 'ctor')
        super(DagsterCompositeType, self).__init__(name, description)

    def evaluate_value(self, value):
        if not isinstance(value, dict):
            return IncomingValueResult.create_failure('Incoming value for composite must be dict')
        return process_incoming_composite_value(self, value, self.ctor)


class ConfigDictionary(DagsterCompositeType):
    def __init__(self, fields):
        super(ConfigDictionary, self).__init__(
            'ConfigDictionary',
            fields,
            lambda val: val,
            '''Configuration dictionary.
            Typed-checked but then passed to implementations as a python dict''',
        )


class IncomingValueResult(namedtuple('_IncomingValueResult', 'success value error_msg')):
    def __new__(cls, success, value, error_msg):
        return super(IncomingValueResult, cls).__new__(
            cls,
            check.bool_param(success, 'success'),
            value,
            check.opt_str_param(error_msg, 'error_msg'),
        )

    @staticmethod
    def create_success(value):
        return IncomingValueResult(success=True, value=value, error_msg=None)

    @staticmethod
    def create_failure(error_msg):
        return IncomingValueResult(success=False, value=None, error_msg=error_msg)


def process_incoming_composite_value(dagster_composite_type, incoming_value, ctor):
    check.inst_param(dagster_composite_type, 'dagster_composite_type', DagsterCompositeType)
    check.dict_param(incoming_value, 'incoming_value', key_type=str)
    # check.str_param(error_context_str, 'error_context_str')
    check.callable_param(ctor, 'ctor')

    field_dict = dagster_composite_type.field_dict

    defined_args = set(field_dict.keys())
    received_args = set(incoming_value.keys())

    for received_arg in received_args:
        if received_arg not in defined_args:
            return IncomingValueResult.create_failure(
                'Field {received} not found. Defined fields: {defined}'.format(
                    defined=repr(defined_args),
                    received=received_arg,
                )
            )

    for expected_field, field_def in field_dict.items():
        if field_def.is_optional:
            continue

        check.invariant(not field_def.default_provided)

        if expected_field not in received_args:
            return IncomingValueResult.create_failure(
                'Did not not find {expected}. Defined fields: {defined}'.format(
                    expected=expected_field,
                    defined=repr(defined_args),
                )
            )

    fields_to_pass = {}

    for expected_field, field_def in field_dict.items():
        if expected_field in received_args:
            evaluation_result = field_def.dagster_type.evaluate_value(
                incoming_value[expected_field]
            )
            if not evaluation_result.success:
                return evaluation_result
            fields_to_pass[expected_field] = evaluation_result.value
        elif field_def.default_provided:
            fields_to_pass[expected_field] = field_def.default_value
        else:
            check.invariant(field_def.is_optional and not field_def.default_provided)

    return IncomingValueResult.create_success(ctor(fields_to_pass))


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
