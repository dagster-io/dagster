from collections import namedtuple
import json
import os
import pickle

from six import integer_types, string_types

from dagster import check
from dagster.core.errors import DagsterRuntimeCoercionError

from .configurable import (
    Configurable,
    ConfigurableFromAny,
    ConfigurableFromList,
    ConfigurableSelectorFromDict,
    ConfigurableObjectFromDict,
    ConfigurableFromScalar,
    ConfigurableFromNullable,
    Field,
)

from .materializable import MaterializeableBuiltinScalar

SerializedTypeValue = namedtuple('SerializedTypeValue', 'name value')


class DagsterTypeAttributes(
    namedtuple('_DagsterTypeAttributes', 'is_builtin is_system_config is_named')
):
    def __new__(cls, is_builtin=False, is_system_config=False, is_named=True):
        return super(DagsterTypeAttributes, cls).__new__(
            cls,
            is_builtin=check.bool_param(is_builtin, 'is_builtin'),
            is_system_config=check.bool_param(is_system_config, 'is_system_config'),
            is_named=check.bool_param(is_named, 'is_named'),
        )


DEFAULT_TYPE_ATTRIBUTES = DagsterTypeAttributes()


class DagsterType(object):
    '''Base class for Dagster Type system. Should be inherited by a subclass.
    Subclass must implement `evaluate_value`

    Attributes:
      name (str): Name of the type

      description (str): Description of the type
    '''

    def __init__(self, name, type_attributes=DEFAULT_TYPE_ATTRIBUTES, description=None):
        self.name = check.str_param(name, 'name')
        self.description = check.opt_str_param(description, 'description')
        self.type_attributes = check.inst_param(
            type_attributes, 'type_attributes', DagsterTypeAttributes
        )
        self.__doc__ = description

    @property
    def is_any(self):
        return isinstance(self, _DagsterAnyType)

    @property
    def is_configurable(self):
        return isinstance(self, Configurable)

    @property
    def is_system_config(self):
        return self.type_attributes.is_system_config

    @property
    def is_named(self):
        return self.type_attributes.is_named

    @property
    def configurable_from_scalar(self):
        check.invariant(not isinstance(self, Configurable))
        return False

    @property
    def configurable_from_dict(self):
        check.invariant(not isinstance(self, Configurable))
        return False

    @property
    def configurable_from_nullable(self):
        check.invariant(not isinstance(self, Configurable))
        return False

    @property
    def configurable_from_list(self):
        check.invariant(not isinstance(self, Configurable))
        return False

    def coerce_runtime_value(self, _value):
        check.not_implemented('Must implement in subclass')

    def iterate_types(self):
        yield self

    def serialize_value(self, output_dir, value):
        type_value = self.create_serializable_type_value(
            self.coerce_runtime_value(value), output_dir
        )
        output_path = os.path.join(output_dir, 'type_value')
        with open(output_path, 'w') as ff:
            json.dump({'type': type_value.name, 'value': type_value.value}, ff)
        return type_value

    def deserialize_value(self, output_dir):
        with open(os.path.join(output_dir, 'type_value'), 'r') as ff:
            type_value_dict = json.load(ff)
            type_value = SerializedTypeValue(
                name=type_value_dict['type'], value=type_value_dict['value']
            )
            if type_value.name != self.name:
                raise Exception('type mismatch')
            return self.deserialize_from_type_value(type_value, output_dir)

    # Override these in subclasses for customizable serialization
    def create_serializable_type_value(self, value, _output_dir):
        return SerializedTypeValue(self.name, value)

    # Override these in subclasses for customizable serialization
    def deserialize_from_type_value(self, type_value, _output_dir):
        return type_value.value


class UncoercedTypeMixin(object):
    '''This is a helper mixin used when you only want to do a type check
    against an in-memory value and then leave that value uncoerced. Only
    is_python_valid_value must be implemented for these classes.
    evaluate_value is implemented for you.
    '''

    def is_python_valid_value(self, _value):
        '''Subclasses must implement this method. Check if the value and output a boolean.

        Returns:
          bool: Whether the value is valid.
        '''
        check.failed('must implement')

    def coerce_runtime_value(self, value):
        if not self.is_python_valid_value(value):
            raise DagsterRuntimeCoercionError(
                'Expected valid value for {type_name} but got {value}'.format(
                    type_name=self.name, value=repr(value)
                )
            )
        return value


class DagsterScalarType(UncoercedTypeMixin, DagsterType):
    '''Base class for dagster types that are scalar python values.

    Attributes:
      name (str): Name of the type

      description (str): Description of the type
    '''


# All builtins are configurable
class DagsterBuiltinScalarType(
    ConfigurableFromScalar, DagsterScalarType, MaterializeableBuiltinScalar
):
    def __init__(self, name, description=None):
        super(DagsterBuiltinScalarType, self).__init__(
            name=name, type_attributes=DagsterTypeAttributes(is_builtin=True), description=None
        )


class _DagsterAnyType(ConfigurableFromAny, UncoercedTypeMixin, DagsterType):
    def __init__(self):
        super(_DagsterAnyType, self).__init__(
            name='Any',
            type_attributes=DagsterTypeAttributes(is_builtin=True),
            description='The type that allows any value, including no value.',
        )

    def is_python_valid_value(self, _value):
        return True


class PythonObjectType(UncoercedTypeMixin, DagsterType):
    '''Dagster Type that checks if the value is an instance of some `python_type`'''

    def __init__(
        self, name, python_type, type_attributes=DEFAULT_TYPE_ATTRIBUTES, description=None
    ):
        super(PythonObjectType, self).__init__(
            name=name, type_attributes=type_attributes, description=description
        )
        self.python_type = check.type_param(python_type, 'python_type')

    def is_python_valid_value(self, value):
        return isinstance(value, self.python_type)

    def serialize_value(self, output_dir, value):
        type_value = self.create_serializable_type_value(
            self.coerce_runtime_value(value), output_dir
        )
        output_path = os.path.join(output_dir, 'type_value')
        with open(output_path, 'w') as ff:
            json.dump({'type': type_value.name, 'path': 'pickle'}, ff)
        pickle_path = os.path.join(output_dir, 'pickle')
        with open(pickle_path, 'wb') as pf:
            pickle.dump(value, pf)

        return type_value

    # If python had final methods, these would be final
    def deserialize_value(self, output_dir):
        with open(os.path.join(output_dir, 'type_value'), 'r') as ff:
            type_value_dict = json.load(ff)
            if type_value_dict['type'] != self.name:
                raise Exception('type mismatch')

        path = type_value_dict['path']
        with open(os.path.join(output_dir, path), 'rb') as pf:
            return pickle.load(pf)


class DagsterStringType(DagsterBuiltinScalarType):
    def is_python_valid_value(self, value):
        return isinstance(value, string_types)


class _DagsterIntType(DagsterBuiltinScalarType):
    def __init__(self):
        super(_DagsterIntType, self).__init__('Int', description='An integer.')

    def is_python_valid_value(self, value):
        if isinstance(value, bool):
            return False

        return isinstance(value, integer_types)


class _DagsterBoolType(DagsterBuiltinScalarType):
    def __init__(self):
        super(_DagsterBoolType, self).__init__('Bool', description='A boolean.')

    def is_python_valid_value(self, value):
        return isinstance(value, bool)


def Nullable(inner_type):
    return _DagsterNullableType(inner_type)


class _DagsterNullableType(ConfigurableFromNullable, DagsterType):
    def __init__(self, inner_type):
        self.inner_type = check.inst_param(inner_type, 'inner_type', DagsterType)
        super(_DagsterNullableType, self).__init__(
            inner_configurable=inner_type,
            name='Nullable.{inner_type}'.format(inner_type=inner_type.name),
            type_attributes=DagsterTypeAttributes(is_builtin=True, is_named=False),
        )

    def coerce_runtime_value(self, value):
        return None if value is None else self.inner_type.coerce_runtime_value(value)

    def iterate_types(self):
        yield self.inner_type


def List(inner_type):
    return _DagsterListType(inner_type)


class _DagsterListType(ConfigurableFromList, DagsterType):
    def __init__(self, inner_type):
        self.inner_type = check.inst_param(inner_type, 'inner_type', DagsterType)
        super(_DagsterListType, self).__init__(
            inner_configurable=inner_type,
            name='List.{inner_type}'.format(inner_type=inner_type.name),
            description='List of {inner_type}'.format(inner_type=inner_type.name),
            type_attributes=DagsterTypeAttributes(is_builtin=True, is_named=False),
        )

    def coerce_runtime_value(self, value):
        if not isinstance(value, list):
            raise DagsterRuntimeCoercionError('Must be a list')

        return list(map(self.inner_type.coerce_runtime_value, value))

    def iterate_types(self):
        yield self.inner_type


# HACK HACK HACK
#
# This is not good and a better solution needs to be found. In order
# for the client-side typeahead in dagit to work as currently structured,
# dictionaries need names. While we deal with that we're going to automatically
# name dictionaries. This will cause odd behavior and bugs is you restart
# the server-side process, the type names changes, and you do not refresh the client.
#
# A possible short term mitigation would to name the dictionary based on the hash
# of its member fields to provide stability in between process restarts.
#
class DictCounter:
    _count = 0

    @staticmethod
    def get_next_count():
        DictCounter._count += 1
        return DictCounter._count


def Dict(fields):
    return _Dict('Dict.' + str(DictCounter.get_next_count()), fields)


def NamedDict(name, fields):
    return _Dict(name, fields)


class _Dict(ConfigurableObjectFromDict, DagsterType):
    '''Configuration dictionary.

    Typed-checked but then passed to implementations as a python dict

    Arguments:
      fields (dict): dictonary of :py:class:`Field` objects keyed by name'''

    def __init__(self, name, fields):
        super(_Dict, self).__init__(
            name=name,
            fields=fields,
            description='A configuration dictionary with typed fields',
            type_attributes=DagsterTypeAttributes(is_named=True, is_builtin=True),
        )

    def coerce_runtime_value(self, value):
        return value


String = DagsterStringType(name='String', description='A string.')
Path = DagsterStringType(
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

# TO DISCUSS: Consolidate with Dict?
PythonDict = PythonObjectType('Dict', dict, type_attributes=DagsterTypeAttributes(is_builtin=True))
