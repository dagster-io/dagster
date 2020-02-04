'''
Serialization & deserialization for Dagster objects.

Why have custom serialization?

* Default json serialization doesn't work well on namedtuples, which we use extensively to create
  immutable value types. Namedtuples serialize like tuples as flat lists.
* Explicit whitelisting should help ensure we are only persisting or communicating across a
  serialization boundary the types we expect to.

Why not pickle?

* This isn't meant to replace pickle in the conditions that pickle is reasonable to use
  (in memory, not human readble, etc) just handle the json case effectively.
'''
import importlib
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import namedtuple
from enum import Enum

import six
import yaml

from dagster import check, seven

_WHITELISTED_TUPLE_MAP = {}
_WHITELISTED_ENUM_MAP = {}


def _whitelist_for_serdes(enum_map, tuple_map):
    def __whitelist_for_serdes(klass):
        if issubclass(klass, Enum):
            enum_map[klass.__name__] = klass
        elif issubclass(klass, tuple):
            tuple_map[klass.__name__] = klass
        else:
            check.failed('Can not whitelist class {klass} for serdes'.format(klass=klass))
        return klass

    return __whitelist_for_serdes


def whitelist_for_serdes(klass):
    return _whitelist_for_serdes(enum_map=_WHITELISTED_ENUM_MAP, tuple_map=_WHITELISTED_TUPLE_MAP)(
        klass
    )


def pack_value(val):
    return _pack_value(val, enum_map=_WHITELISTED_ENUM_MAP, tuple_map=_WHITELISTED_TUPLE_MAP)


def _pack_value(val, enum_map, tuple_map):
    if isinstance(val, list):
        return [_pack_value(i, enum_map, tuple_map) for i in val]
    if isinstance(val, tuple):
        klass_name = val.__class__.__name__
        check.invariant(
            klass_name in tuple_map,
            'Can only serialize whitelisted namedtuples, recieved {}'.format(klass_name),
        )
        base_dict = {
            key: _pack_value(value, enum_map, tuple_map) for key, value in val._asdict().items()
        }
        base_dict['__class__'] = klass_name
        return base_dict
    if isinstance(val, Enum):
        klass_name = val.__class__.__name__
        check.invariant(
            klass_name in enum_map,
            'Can only serialize whitelisted Enums, recieved {}'.format(klass_name),
        )
        return {'__enum__': str(val)}
    if isinstance(val, dict):
        return {key: _pack_value(value, enum_map, tuple_map) for key, value in val.items()}

    return val


def _serialize_dagster_namedtuple(nt, enum_map, tuple_map):
    return seven.json.dumps(_pack_value(nt, enum_map, tuple_map))


def serialize_dagster_namedtuple(nt):
    return _serialize_dagster_namedtuple(
        nt, enum_map=_WHITELISTED_ENUM_MAP, tuple_map=_WHITELISTED_TUPLE_MAP
    )


def unpack_value(val):
    return _unpack_value(val, enum_map=_WHITELISTED_ENUM_MAP, tuple_map=_WHITELISTED_TUPLE_MAP)


def _unpack_value(val, enum_map, tuple_map):
    if isinstance(val, list):
        return [_unpack_value(i, enum_map, tuple_map) for i in val]
    if isinstance(val, dict) and val.get('__class__'):
        klass_name = val.pop('__class__')
        klass = tuple_map[klass_name]
        unpacked_val = {
            key: _unpack_value(value, enum_map, tuple_map) for key, value in val.items()
        }

        # Naively implements backwards compatibility by filtering arguments that aren't present in
        # the constructor. If a property is present in the serialized object, but doesn't exist in
        # the version of the class loaded into memory, that property will be completely ignored.
        # The call to seven.get_args turns out to be pretty expensive -- we should probably turn
        # to, e.g., manually managing the deprecated keys on the serdes constructor.
        args_for_class = seven.get_args(klass)
        filtered_val = {k: v for k, v in unpacked_val.items() if k in args_for_class}
        return klass(**filtered_val)
    if isinstance(val, dict) and val.get('__enum__'):
        name, member = val['__enum__'].split('.')
        return getattr(enum_map[name], member)
    if isinstance(val, dict):
        return {key: _unpack_value(value, enum_map, tuple_map) for key, value in val.items()}

    return val


def deserialize_json_to_dagster_namedtuple(json_str):
    return _deserialize_json_to_dagster_namedtuple(
        check.str_param(json_str, 'json_str'),
        enum_map=_WHITELISTED_ENUM_MAP,
        tuple_map=_WHITELISTED_TUPLE_MAP,
    )


def _deserialize_json_to_dagster_namedtuple(json_str, enum_map, tuple_map):
    return _unpack_value(seven.json.loads(json_str), enum_map=enum_map, tuple_map=tuple_map)


@whitelist_for_serdes
class ConfigurableClassData(
    namedtuple('_ConfigurableClassData', 'module_name class_name config_yaml')
):
    '''Serializable tuple describing where to find a class and the config fragment that should
    be used to instantiate it.

    Users should not instantiate this class directly.
    
    Classes intended to be serialized in this way should implement the 
    :py:class:`dagster.serdes.ConfigurableClass` mixin.
    '''

    def __new__(cls, module_name, class_name, config_yaml):
        return super(ConfigurableClassData, cls).__new__(
            cls,
            check.str_param(module_name, 'module_name'),
            check.str_param(class_name, 'class_name'),
            check.str_param(config_yaml, 'config_yaml'),
        )

    def info_str(self, prefix=''):
        return (
            '{p}module: {module}\n'
            '{p}class: {cls}\n'
            '{p}config:\n'
            '{p}  {config}'.format(
                p=prefix, module=self.module_name, cls=self.class_name, config=self.config_yaml
            )
        )

    def rehydrate(self):
        from dagster.core.errors import DagsterInvalidConfigError
        from dagster.config.field import resolve_to_config_type
        from dagster.config.validate import process_config

        try:
            module = importlib.import_module(self.module_name)
        except seven.ModuleNotFoundError:
            check.failed(
                'Couldn\'t import module {module_name} when attempting to rehydrate the '
                'configurable class {configurable_class}'.format(
                    module_name=self.module_name,
                    configurable_class=self.module_name + '.' + self.class_name,
                )
            )
        try:
            klass = getattr(module, self.class_name)
        except AttributeError:
            check.failed(
                'Couldn\'t find class {class_name} in module when attempting to rehydrate the '
                'configurable class {configurable_class}'.format(
                    class_name=self.class_name,
                    configurable_class=self.module_name + '.' + self.class_name,
                )
            )

        if not issubclass(klass, ConfigurableClass):
            raise check.CheckError(
                klass,
                'class {class_name} in module {module_name}'.format(
                    class_name=self.class_name, module_name=self.module_name
                ),
                ConfigurableClass,
            )

        config_dict = yaml.safe_load(self.config_yaml)
        result = process_config(resolve_to_config_type(klass.config_type()), config_dict)
        if not result.success:
            raise DagsterInvalidConfigError(
                'Errors whilst loading configuration for {}.'.format(klass.config_type()),
                result.errors,
                config_dict,
            )
        return klass.from_config_value(self, result.value)


class ConfigurableClass(six.with_metaclass(ABCMeta)):
    '''Abstract mixin for classes that can be rehydrated from config.

    This supports a powerful plugin pattern which avoids both a) a lengthy, hard-to-synchronize list
    of conditional imports / optional extras_requires in dagster core and b) a magic directory or
    file in which third parties can place plugin packages. Instead, the intention is to make, e.g.,
    run storage, pluggable with a config chunk like:

    .. code-block:: yaml

        run_storage:
            module: very_cool_package.run_storage
            class: SplendidRunStorage
            config:
                magic_word: "quux"

    This same pattern should eventually be viable for other system components, e.g. engines.

    The ConfigurableClass mixin provides the necessary hooks for classes to be instantiated from
    an instance of ConfigurableClassData.

    Pieces of the Dagster system which we wish to make pluggable in this way should consume a config
    type such as:

    .. code-block:: python

        {'module': str, 'class': str, 'config': Field(Permissive())}

    '''

    @abstractproperty
    def inst_data(self):
        '''
        Subclass must be able to return the inst_data as a property if it has been constructed
        through the from_config_value code path.
        '''

    @classmethod
    @abstractmethod
    def config_type(cls):
        '''dagster.ConfigType: The config type against which to validate a config yaml fragment
        serialized in an instance of ConfigurableClassData.
        '''

    @staticmethod
    @abstractmethod
    def from_config_value(inst_data, config_value):
        '''New up an instance of the ConfigurableClass from a validated config value.

        Called by ConfigurableClassData.rehydrate.

        Args:
            config_value (dict): The validated config value to use. Typically this should be the
                `value` attribute of a dagster.core.types.evaluator.evaluation.EvaluateValueResult.


        A common pattern is for the implementation to align the config_value with the signature
        of the ConfigurableClass's constructor:

        .. code-block:: python

            @staticmethod
            def from_config_value(inst_data, config_value):
                return MyConfigurableClass(inst_data=inst_data, **config_value)

        '''
