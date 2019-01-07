from collections import namedtuple
import json
import os

from dagster import check
from dagster.core.errors import DagsterRuntimeCoercionError

# other files depend on the Field include
# pylint: disable=W0611
from .configurable import (
    Configurable,
    ConfigurableFromAny,
    ConfigurableFromList,
    ConfigurableFromDict,
    ConfigurableObjectFromDict,
    ConfigurableFromScalar,
    ConfigurableFromNullable,
    Field,
)

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
        # Does not appear to be strictly necessary but coding defensively because of the
        # issues here: https://github.com/sphinx-doc/sphinx/issues/5870
        #
        # May be worth evaluating whether doing this is good idea at all.
        if description is not None:
            self.__doc__ = description

    @property
    def is_any(self):
        return False

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
