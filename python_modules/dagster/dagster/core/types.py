from collections import namedtuple
import json
import os
import pickle

from six import integer_types, string_types

from dagster import check
from dagster.core.errors import (
    DagsterEvaluateConfigValueError,
    DagsterRuntimeCoercionError,
)

SerializedTypeValue = namedtuple('SerializedTypeValue', 'name value')


class DagsterTypeAttributes(namedtuple('_DagsterTypeAttributes', 'is_builtin is_system_config')):
    def __new__(cls, is_builtin=False, is_system_config=False):
        return super(DagsterTypeAttributes, cls).__new__(
            cls,
            is_builtin=check.bool_param(is_builtin, 'is_builtin'),
            is_system_config=check.bool_param(is_system_config, 'is_system_config'),
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
            type_attributes,
            'type_attributes',
            DagsterTypeAttributes,
        )
        self.__doc__ = description

    def __repr__(self):
        return 'DagsterType({name})'.format(name=self.name)

    def coerce_runtime_value(self, _value):
        check.not_implemented('Must implement in subclass')

    def construct_from_config_value(self, config_value):
        return config_value

    def iterate_types(self):
        yield self

    def serialize_value(self, output_dir, value):
        type_value = self.create_serializable_type_value(
            self.coerce_runtime_value(value),
            output_dir,
        )
        output_path = os.path.join(output_dir, 'type_value')
        with open(output_path, 'w') as ff:
            json.dump(
                {
                    'type': type_value.name,
                    'value': type_value.value,
                },
                ff,
            )
        return type_value

    def deserialize_value(self, output_dir):
        with open(os.path.join(output_dir, 'type_value'), 'r') as ff:
            type_value_dict = json.load(ff)
            type_value = SerializedTypeValue(
                name=type_value_dict['type'],
                value=type_value_dict['value'],
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
                    type_name=self.name,
                    value=repr(value),
                ),
            )
        return value


class DagsterScalarType(UncoercedTypeMixin, DagsterType):
    '''Base class for dagster types that are scalar python values.

    Attributes:
      name (str): Name of the type

      description (str): Description of the type
    '''


class DagsterBuiltinScalarType(DagsterScalarType):
    def __init__(self, name, description=None):
        super(DagsterBuiltinScalarType, self).__init__(
            name=name,
            type_attributes=DagsterTypeAttributes(is_builtin=True),
            description=None,
        )


class _DagsterAnyType(UncoercedTypeMixin, DagsterType):
    def __init__(self):
        super(_DagsterAnyType, self).__init__(
            name='Any',
            type_attributes=DagsterTypeAttributes(is_builtin=True),
            description='The type that allows any value, including no value.',
        )

    def is_python_valid_value(self, _value):
        return True


def nullable_isinstance(value, typez):
    return value is None or isinstance(value, typez)


class PythonObjectType(UncoercedTypeMixin, DagsterType):
    '''Dagster Type that checks if the value is an instance of some `python_type`'''

    def __init__(
        self,
        name,
        python_type,
        type_attributes=DEFAULT_TYPE_ATTRIBUTES,
        description=None,
    ):
        super(PythonObjectType, self).__init__(
            name=name,
            type_attributes=type_attributes,
            description=description,
        )
        self.python_type = check.type_param(python_type, 'python_type')

    def is_python_valid_value(self, value):
        return nullable_isinstance(value, self.python_type)

    def serialize_value(self, output_dir, value):
        type_value = self.create_serializable_type_value(
            self.coerce_runtime_value(value), output_dir
        )
        output_path = os.path.join(output_dir, 'type_value')
        with open(output_path, 'w') as ff:
            json.dump(
                {
                    'type': type_value.name,
                    'path': 'pickle'
                },
                ff,
            )
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
        return nullable_isinstance(value, string_types)


class _DagsterIntType(DagsterBuiltinScalarType):
    def __init__(self):
        super(_DagsterIntType, self).__init__('Int', description='An integer.')

    def is_python_valid_value(self, value):
        if isinstance(value, bool):
            return False
        return nullable_isinstance(value, integer_types)


class _DagsterBoolType(DagsterBuiltinScalarType):
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
        description=None,
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
        self._default_value = default_value

    @property
    def default_provided(self):
        '''Was a default value provided

        Returns:
            bool: Yes or no
        '''
        return self._default_value != FIELD_NO_DEFAULT_PROVIDED

    @property
    def default_value(self):
        check.invariant(
            self.default_provided,
            'Asking for default value when none was provided',
        )

        if callable(self._default_value):
            return self._default_value()

        return self._default_value

    @property
    def default_value_as_str(self):
        check.invariant(
            self.default_provided,
            'Asking for default value when none was provided',
        )

        if callable(self._default_value):
            return repr(self._default_value)

        return str(self._default_value)


class FieldDefinitionDictionary(dict):
    def __init__(self, ddict):
        check.dict_param(ddict, 'ddict', key_type=str, value_type=Field)
        super(FieldDefinitionDictionary, self).__init__(ddict)

    def __setitem__(self, _key, _value):
        check.failed('This dictionary is readonly')


class DagsterCompositeType(DagsterType):
    '''Dagster type representing a type with a list of named :py:class:`Field` objects.
    '''

    def __init__(
        self,
        name,
        fields,
        description=None,
        type_attributes=DEFAULT_TYPE_ATTRIBUTES,
    ):
        self.field_dict = FieldDefinitionDictionary(fields)
        super(DagsterCompositeType, self).__init__(
            name=name,
            description=description,
            type_attributes=type_attributes,
        )

    def coerce_runtime_value(self, value):
        from .evaluator import throwing_evaluate_config_value
        return throwing_evaluate_config_value(self, value)

    def iterate_types(self):
        for field_type in self.field_dict.values():
            for inner_type in field_type.dagster_type.iterate_types():
                yield inner_type
        yield self

    @property
    def all_fields_optional(self):
        for field in self.field_dict.values():
            if not field.is_optional:
                return False
        return True

    @property
    def field_name_set(self):
        return set(self.field_dict.keys())


class DagsterSelectorType(DagsterCompositeType):  # TODO: This inheritance sucks
    pass


class IsScopedConfigType:
    def __init__(self):
        check.invariant(
            hasattr(
                self,
                '_scoped_config_info',
                (
                    'If you use IsScopedConfigType mixin the target class must '
                    'have _scoped_config_info property'
                ),
            ),
        )

    @property
    def scoped_config_info(self):
        return self._scoped_config_info  # pylint: disable=E1101


class ConfigDictionary(DagsterCompositeType, IsScopedConfigType):
    '''Configuration dictionary.

    Typed-checked but then passed to implementations as a python dict

    Arguments:
      fields (dict): dictonary of :py:class:`Field` objects keyed by name'''

    def __init__(self, name, fields, scoped_config_info=None):
        self._scoped_config_info = check.opt_inst_param(
            scoped_config_info,
            'scoped_config_info',
            ScopedConfigInfo,
        )
        super(ConfigDictionary, self).__init__(
            name,
            fields,
            'A configuration dictionary with typed fields',
        )

    def coerce_runtime_value(self, value):
        if value is not None and not isinstance(value, dict):
            raise DagsterRuntimeCoercionError('Incoming value for composite must be dict')
        ## TODO make this return value
        from .evaluator import throwing_evaluate_config_value
        return throwing_evaluate_config_value(self, value)


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
Dict = PythonObjectType('Dict', dict, type_attributes=DagsterTypeAttributes(is_builtin=True))


class ScopedConfigInfo(
    namedtuple(
        '_ConfigScopeInfo',
        'pipeline_def_name solid_def_name context_def_name',
    ),
):
    def __new__(cls, pipeline_def_name, solid_def_name=None, context_def_name=None):
        check.str_param(pipeline_def_name, 'pipeline_def_name')
        check.opt_str_param(solid_def_name, 'solid_def_name')
        check.opt_str_param(context_def_name, 'context_def_name')

        check.invariant(
            bool(solid_def_name or context_def_name),
            'One of solid or context must be specified',
        )
        check.invariant(
            not (solid_def_name and context_def_name),
            'Both solid and context cannot be specified',
        )

        return super(ScopedConfigInfo, cls).__new__(
            cls,
            pipeline_def_name,
            solid_def_name,
            context_def_name,
        )
