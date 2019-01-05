import json
import os
import pickle

import six

from dagster import check

from dagster.core.errors import DagsterRuntimeCoercionError

from .base import (
    DagsterType,
    DagsterScalarType,
    UncoercedTypeMixin,
    DEFAULT_TYPE_ATTRIBUTES,
    DagsterTypeAttributes,
)

from .configurable import (
    ConfigurableSelectorFromDict,
    ConfigurableObjectFromDict,
    ConfigurableFromScalar,
    ConfigurableFromAny,
    ConfigurableFromNullable,
    ConfigurableFromList,
    Field,
)

from .materializable import Materializeable


class MaterializeableBuiltinScalar(Materializeable):
    def __init__(self, *args, **kwargs):
        super(MaterializeableBuiltinScalar, self).__init__(*args, **kwargs)
        self.config_schema = None

    def define_materialization_config_schema(self):
        if self.config_schema is None:
            # This has to be applied to a dagster type so name is available
            # pylint: disable=E1101
            self.config_schema = MaterializeableBuiltinScalarConfigSchema(
                '{name}.MaterializationSchema'.format(name=self.name)
            )
        return self.config_schema

    def materialize_runtime_value(self, config_spec, runtime_value):
        check.dict_param(config_spec, 'config_spec')
        selector_key, selector_value = list(config_spec.items())[0]

        if selector_key == 'json':
            json_file_path = selector_value['path']
            json_value = json.dumps({'value': runtime_value})
            with open(json_file_path, 'w') as ff:
                ff.write(json_value)
        else:
            check.failed(
                'Unsupported selector key: {selector_key}'.format(selector_key=selector_key)
            )


def define_path_dict_field():
    return Field(Dict({'path': Field(Path)}))


class MaterializeableBuiltinScalarConfigSchema(ConfigurableSelectorFromDict, DagsterType):
    def __init__(self, name):
        super(MaterializeableBuiltinScalarConfigSchema, self).__init__(
            name=name,
            description='Materialization schema for scalar ' + name,
            fields={'json': define_path_dict_field()},
        )


# All builtins are configurable
class DagsterBuiltinScalarType(
    ConfigurableFromScalar, MaterializeableBuiltinScalar, DagsterScalarType
):
    def __init__(self, name, description=None):
        super(DagsterBuiltinScalarType, self).__init__(
            name=name,
            type_attributes=DagsterTypeAttributes(is_builtin=True),
            description=description,
        )


class _DagsterAnyType(ConfigurableFromAny, UncoercedTypeMixin, DagsterType):
    def __init__(self):
        super(_DagsterAnyType, self).__init__(
            name='Any',
            type_attributes=DagsterTypeAttributes(is_builtin=True),
            description='The type that allows any value, including no value.',
        )

    @property
    def is_any(self):
        return True

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
        return isinstance(value, six.string_types)


class _DagsterIntType(DagsterBuiltinScalarType):
    def __init__(self):
        super(_DagsterIntType, self).__init__('Int', description='An integer.')

    def is_python_valid_value(self, value):
        if isinstance(value, bool):
            return False

        return isinstance(value, six.integer_types)


class _DagsterBoolType(DagsterBuiltinScalarType):
    def __init__(self):
        super(_DagsterBoolType, self).__init__('Bool', description='A boolean.')

    def is_python_valid_value(self, value):
        return isinstance(value, bool)


def Nullable(inner_type):
    return _DagsterNullableType(inner_type)


def is_wrapping_type(dagster_type):
    return isinstance(dagster_type, (_DagsterNullableType, _DagsterListType))


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
