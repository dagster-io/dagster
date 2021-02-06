"""
Serialization & deserialization for Dagster objects.

Why have custom serialization?

* Default json serialization doesn't work well on namedtuples, which we use extensively to create
  immutable value types. Namedtuples serialize like tuples as flat lists.
* Explicit whitelisting should help ensure we are only persisting or communicating across a
  serialization boundary the types we expect to.

Why not pickle?

* This isn't meant to replace pickle in the conditions that pickle is reasonable to use
  (in memory, not human readable, etc) just handle the json case effectively.
"""
import hashlib
import importlib
import sys
from abc import ABC, abstractmethod, abstractproperty
from collections import namedtuple
from enum import Enum
from inspect import Parameter, signature

import yaml
from dagster import check, seven
from dagster.utils import compose

_WHITELIST_MAP = {
    "types": {"tuple": {}, "enum": {}},
    "persistence": {},
}


def create_snapshot_id(snapshot):
    json_rep = serialize_dagster_namedtuple(snapshot)
    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    m.update(json_rep.encode("utf-8"))
    return m.hexdigest()


def serialize_pp(value):
    return serialize_dagster_namedtuple(value, indent=2, separators=(",", ": "))


def register_serdes_tuple_fallbacks(fallback_map):
    for class_name, klass in fallback_map.items():
        _WHITELIST_MAP["types"]["tuple"][class_name] = klass


def _get_dunder_new_params_dict(klass):
    return signature(klass.__new__).parameters


def _get_dunder_new_params(klass):
    return list(_get_dunder_new_params_dict(klass).values())


class SerdesClassUsageError(Exception):
    pass


class Persistable(ABC):
    def to_storage_value(self):
        return default_to_storage_value(self, _WHITELIST_MAP)

    @classmethod
    def from_storage_dict(cls, storage_dict):
        return default_from_storage_dict(cls, storage_dict)


def _check_serdes_tuple_class_invariants(klass):
    dunder_new_params = _get_dunder_new_params(klass)

    cls_param = dunder_new_params[0]

    def _with_header(msg):
        return "For namedtuple {class_name}: {msg}".format(class_name=klass.__name__, msg=msg)

    if cls_param.name not in {"cls", "_cls"}:
        raise SerdesClassUsageError(
            _with_header(
                'First parameter must be _cls or cls. Got "{name}".'.format(name=cls_param.name)
            )
        )

    value_params = dunder_new_params[1:]

    for index, field in enumerate(klass._fields):

        if index >= len(value_params):
            error_msg = (
                "Missing parameters to __new__. You have declared fields "
                "in the named tuple that are not present as parameters to the "
                "to the __new__ method. In order for "
                "both serdes serialization and pickling to work, "
                "these must match. Missing: {missing_fields}"
            ).format(missing_fields=repr(list(klass._fields[index:])))

            raise SerdesClassUsageError(_with_header(error_msg))

        value_param = value_params[index]
        if value_param.name != field:
            error_msg = (
                "Params to __new__ must match the order of field declaration in the namedtuple. "
                'Declared field number {one_based_index} in the namedtuple is "{field_name}". '
                'Parameter {one_based_index} in __new__ method is "{param_name}".'
            ).format(one_based_index=index + 1, field_name=field, param_name=value_param.name)
            raise SerdesClassUsageError(_with_header(error_msg))

    if len(value_params) > len(klass._fields):
        # Ensure that remaining parameters have default values
        for extra_param_index in range(len(klass._fields), len(value_params) - 1):
            if value_params[extra_param_index].default == Parameter.empty:
                error_msg = (
                    'Parameter "{param_name}" is a parameter to the __new__ '
                    "method but is not a field in this namedtuple. The only "
                    "reason why this should exist is that "
                    "it is a field that used to exist (we refer to this as the graveyard) "
                    "but no longer does. However it might exist in historical storage. This "
                    "parameter existing ensures that serdes continues to work. However these "
                    "must come at the end and have a default value for pickling to work."
                ).format(param_name=value_params[extra_param_index].name)
                raise SerdesClassUsageError(_with_header(error_msg))


def _whitelist_for_persistence(whitelist_map):
    def __whitelist_for_persistence(klass):
        check.subclass_param(klass, "klass", Persistable)
        whitelist_map["persistence"][klass.__name__] = klass
        return klass

    return __whitelist_for_persistence


def _whitelist_for_serdes(whitelist_map):
    def __whitelist_for_serdes(klass):
        if issubclass(klass, Enum):
            whitelist_map["types"]["enum"][klass.__name__] = klass
        elif issubclass(klass, tuple):
            _check_serdes_tuple_class_invariants(klass)
            whitelist_map["types"]["tuple"][klass.__name__] = klass
        else:
            check.failed("Can not whitelist class {klass} for serdes".format(klass=klass))

        return klass

    return __whitelist_for_serdes


def whitelist_for_serdes(klass):
    check.class_param(klass, "klass")
    return _whitelist_for_serdes(whitelist_map=_WHITELIST_MAP)(klass)


def whitelist_for_persistence(klass):
    check.class_param(klass, "klass")
    return compose(
        _whitelist_for_persistence(whitelist_map=_WHITELIST_MAP),
        _whitelist_for_serdes(whitelist_map=_WHITELIST_MAP),
    )(klass)


def pack_value(val):
    return _pack_value(val, whitelist_map=_WHITELIST_MAP)


def _pack_value(val, whitelist_map):
    if isinstance(val, list):
        return [_pack_value(i, whitelist_map) for i in val]
    if isinstance(val, tuple):
        klass_name = val.__class__.__name__
        check.invariant(
            klass_name in whitelist_map["types"]["tuple"],
            "Can only serialize whitelisted namedtuples, received tuple {}".format(val),
        )
        if klass_name in whitelist_map["persistence"]:
            return val.to_storage_value()
        base_dict = {key: _pack_value(value, whitelist_map) for key, value in val._asdict().items()}
        base_dict["__class__"] = klass_name
        return base_dict
    if isinstance(val, Enum):
        klass_name = val.__class__.__name__
        check.invariant(
            klass_name in whitelist_map["types"]["enum"],
            "Can only serialize whitelisted Enums, received {}".format(klass_name),
        )
        return {"__enum__": str(val)}
    if isinstance(val, set):
        return {"__set__": [_pack_value(item, whitelist_map) for item in val]}
    if isinstance(val, frozenset):
        return {"__frozenset__": [_pack_value(item, whitelist_map) for item in val]}
    if isinstance(val, dict):
        return {key: _pack_value(value, whitelist_map) for key, value in val.items()}

    return val


def _serialize_dagster_namedtuple(nt, whitelist_map, **json_kwargs):
    return seven.json.dumps(_pack_value(nt, whitelist_map), **json_kwargs)


def serialize_value(val):
    return seven.json.dumps(_pack_value(val, whitelist_map=_WHITELIST_MAP))


def deserialize_value(val):
    return _unpack_value(
        seven.json.loads(check.str_param(val, "val")),
        whitelist_map=_WHITELIST_MAP,
    )


def serialize_dagster_namedtuple(nt, **json_kwargs):
    return _serialize_dagster_namedtuple(
        check.tuple_param(nt, "nt"), whitelist_map=_WHITELIST_MAP, **json_kwargs
    )


def unpack_value(val):
    return _unpack_value(val, whitelist_map=_WHITELIST_MAP)


def _unpack_value(val, whitelist_map):
    if isinstance(val, list):
        return [_unpack_value(i, whitelist_map) for i in val]
    if isinstance(val, dict) and val.get("__class__"):
        klass_name = val.pop("__class__")

        check.invariant(
            klass_name in whitelist_map["types"]["tuple"],
            (
                f'Attempted to deserialize class "{klass_name}", which is not in '
                "the serdes whitelist."
            ),
        )

        klass = whitelist_map["types"]["tuple"][klass_name]
        if klass is None:
            return None

        unpacked_val = {key: _unpack_value(value, whitelist_map) for key, value in val.items()}

        if klass_name in whitelist_map["persistence"]:
            return klass.from_storage_dict(unpacked_val)

        # Naively implements backwards compatibility by filtering arguments that aren't present in
        # the constructor. If a property is present in the serialized object, but doesn't exist in
        # the version of the class loaded into memory, that property will be completely ignored.
        # The call to seven.get_args turns out to be pretty expensive -- we should probably turn
        # to, e.g., manually managing the deprecated keys on the serdes constructor.
        args_for_class = seven.get_args(klass)
        filtered_val = {k: v for k, v in unpacked_val.items() if k in args_for_class}
        return klass(**filtered_val)
    if isinstance(val, dict) and val.get("__enum__"):
        name, member = val["__enum__"].split(".")
        return getattr(whitelist_map["types"]["enum"][name], member)
    if isinstance(val, dict) and val.get("__set__") is not None:
        return set([_unpack_value(item, whitelist_map) for item in val["__set__"]])
    if isinstance(val, dict) and val.get("__frozenset__") is not None:
        return frozenset([_unpack_value(item, whitelist_map) for item in val["__frozenset__"]])
    if isinstance(val, dict):
        return {key: _unpack_value(value, whitelist_map) for key, value in val.items()}

    return val


def deserialize_json_to_dagster_namedtuple(json_str):
    dagster_namedtuple = _deserialize_json_to_dagster_namedtuple(
        check.str_param(json_str, "json_str"),
        whitelist_map=_WHITELIST_MAP,
    )
    check.invariant(
        isinstance(dagster_namedtuple, tuple),
        "Output of deserialized json_str was not a namedtuple. Received type {}.".format(
            type(dagster_namedtuple)
        ),
    )
    return dagster_namedtuple


def _deserialize_json_to_dagster_namedtuple(json_str, whitelist_map):
    return _unpack_value(seven.json.loads(json_str), whitelist_map=whitelist_map)


def default_to_storage_value(value, whitelist_map):
    base_dict = {key: _pack_value(value, whitelist_map) for key, value in value._asdict().items()}
    base_dict["__class__"] = value.__class__.__name__
    return base_dict


def default_from_storage_dict(cls, storage_dict):
    return cls.__new__(cls, **storage_dict)


@whitelist_for_serdes
class ConfigurableClassData(
    namedtuple("_ConfigurableClassData", "module_name class_name config_yaml")
):
    """Serializable tuple describing where to find a class and the config fragment that should
    be used to instantiate it.

    Users should not instantiate this class directly.

    Classes intended to be serialized in this way should implement the
    :py:class:`dagster.serdes.ConfigurableClass` mixin.
    """

    def __new__(cls, module_name, class_name, config_yaml):
        return super(ConfigurableClassData, cls).__new__(
            cls,
            check.str_param(module_name, "module_name"),
            check.str_param(class_name, "class_name"),
            check.str_param(config_yaml, "config_yaml"),
        )

    def info_dict(self):
        return {
            "module": self.module_name,
            "class": self.class_name,
            "config": yaml.safe_load(self.config_yaml),
        }

    def rehydrate(self):
        from dagster.core.errors import DagsterInvalidConfigError
        from dagster.config.field import resolve_to_config_type
        from dagster.config.validate import process_config

        try:
            module = importlib.import_module(self.module_name)
        except ModuleNotFoundError:
            check.failed(
                "Couldn't import module {module_name} when attempting to load the "
                "configurable class {configurable_class}".format(
                    module_name=self.module_name,
                    configurable_class=self.module_name + "." + self.class_name,
                )
            )
        try:
            klass = getattr(module, self.class_name)
        except AttributeError:
            check.failed(
                "Couldn't find class {class_name} in module when attempting to load the "
                "configurable class {configurable_class}".format(
                    class_name=self.class_name,
                    configurable_class=self.module_name + "." + self.class_name,
                )
            )

        if not issubclass(klass, ConfigurableClass):
            raise check.CheckError(
                klass,
                "class {class_name} in module {module_name}".format(
                    class_name=self.class_name, module_name=self.module_name
                ),
                ConfigurableClass,
            )

        config_dict = yaml.safe_load(self.config_yaml)
        result = process_config(resolve_to_config_type(klass.config_type()), config_dict)
        if not result.success:
            raise DagsterInvalidConfigError(
                "Errors whilst loading configuration for {}.".format(klass.config_type()),
                result.errors,
                config_dict,
            )
        return klass.from_config_value(self, result.value)


class ConfigurableClass(ABC):
    """Abstract mixin for classes that can be loaded from config.

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

    The ``ConfigurableClass`` mixin provides the necessary hooks for classes to be instantiated from
    an instance of ``ConfigurableClassData``.

    Pieces of the Dagster system which we wish to make pluggable in this way should consume a config
    type such as:

    .. code-block:: python

        {'module': str, 'class': str, 'config': Field(Permissive())}

    """

    @abstractproperty
    def inst_data(self):
        """
        Subclass must be able to return the inst_data as a property if it has been constructed
        through the from_config_value code path.
        """

    @classmethod
    @abstractmethod
    def config_type(cls):
        """dagster.ConfigType: The config type against which to validate a config yaml fragment
        serialized in an instance of ``ConfigurableClassData``.
        """

    @staticmethod
    @abstractmethod
    def from_config_value(inst_data, config_value):
        """New up an instance of the ConfigurableClass from a validated config value.

        Called by ConfigurableClassData.rehydrate.

        Args:
            config_value (dict): The validated config value to use. Typically this should be the
                ``value`` attribute of a
                :py:class:`~dagster.core.types.evaluator.evaluation.EvaluateValueResult`.


        A common pattern is for the implementation to align the config_value with the signature
        of the ConfigurableClass's constructor:

        .. code-block:: python

            @staticmethod
            def from_config_value(inst_data, config_value):
                return MyConfigurableClass(inst_data=inst_data, **config_value)

        """
