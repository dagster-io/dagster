# encoding: utf-8
import hashlib
import os
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Mapping, Optional, Sequence, Type

import dagster._check as check
from dagster._annotations import public
from dagster._core.errors import DagsterInvalidConfigDefinitionError

from .config_type import Array, ConfigType, ConfigTypeKind

if TYPE_CHECKING:
    from dagster._config import Field


def all_optional_type(config_type: ConfigType) -> bool:
    check.inst_param(config_type, "config_type", ConfigType)

    if ConfigTypeKind.is_shape(config_type.kind):
        for field in config_type.fields.values():  # type: ignore
            if field.is_required:
                return False
        return True

    if ConfigTypeKind.is_selector(config_type.kind):
        if len(config_type.fields) == 1:  # type: ignore
            for field in config_type.fields.values():  # type: ignore
                if field.is_required:
                    return False
            return True

    return False


class __FieldValueSentinel:
    pass


class __InferOptionalCompositeFieldSentinel:
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel

INFER_OPTIONAL_COMPOSITE_FIELD = __InferOptionalCompositeFieldSentinel


class _ConfigHasFields(ConfigType):
    def __init__(self, fields, **kwargs):
        self.fields = expand_fields_dict(fields)
        super(_ConfigHasFields, self).__init__(**kwargs)

    def type_iterator(self) -> Iterator["ConfigType"]:
        for field in self.fields.values():
            yield from field.config_type.type_iterator()
        yield from super().type_iterator()


FIELD_HASH_CACHE: Dict[str, Any] = {}


def _memoize_inst_in_field_cache(passed_cls, defined_cls, key):
    if key in FIELD_HASH_CACHE:
        return FIELD_HASH_CACHE[key]

    defined_cls_inst = super(defined_cls, passed_cls).__new__(defined_cls)
    defined_cls_inst._initialized = False  # noqa: SLF001
    FIELD_HASH_CACHE[key] = defined_cls_inst
    return defined_cls_inst


def _add_hash(m, string):
    m.update(string.encode("utf-8"))


def compute_fields_hash(fields, description, field_aliases=None):
    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    if description:
        _add_hash(m, ":description: " + description)

    for field_name in sorted(list(fields.keys())):
        field = fields[field_name]
        _add_hash(m, ":fieldname:" + field_name)
        if field.default_provided:
            _add_hash(m, ":default_value: " + field.default_value_as_json_str)
        _add_hash(m, ":is_required: " + str(field.is_required))
        _add_hash(m, ":type_key: " + field.config_type.key)
        if field.description:
            _add_hash(m, ":description: " + field.description)

    field_aliases = check.opt_dict_param(
        field_aliases, "field_aliases", key_type=str, value_type=str
    )
    for field_name in sorted(list(field_aliases.keys())):
        field_alias = field_aliases[field_name]
        _add_hash(m, ":fieldname: " + field_name)
        _add_hash(m, ":fieldalias: " + field_alias)

    return m.hexdigest()


def _define_shape_key_hash(fields, description, field_aliases):
    return "Shape." + compute_fields_hash(fields, description, field_aliases=field_aliases)


class Shape(_ConfigHasFields):
    """Schema for configuration data with string keys and typed values via :py:class:`Field`.

    Unlike :py:class:`Permissive`, unspecified fields are not allowed and will throw a
    :py:class:`~dagster.DagsterInvalidConfigError`.

    Args:
        fields (Dict[str, Field]):
            The specification of the config dict.
        field_aliases (Dict[str, str]):
            Maps a string key to an alias that can be used instead of the original key. For example,
            an entry {"foo": "bar"} means that someone could use "bar" instead of "foo" as a
            top level string key.
    """

    def __new__(
        cls,
        fields,
        description=None,
        field_aliases=None,
    ):
        return _memoize_inst_in_field_cache(
            cls,
            Shape,
            _define_shape_key_hash(expand_fields_dict(fields), description, field_aliases),
        )

    def __init__(
        self,
        fields,
        description=None,
        field_aliases=None,
    ):
        # if we hit in the field cache - skip double init
        if self._initialized:
            return

        fields = expand_fields_dict(fields)
        super(Shape, self).__init__(
            kind=ConfigTypeKind.STRICT_SHAPE,
            key=_define_shape_key_hash(fields, description, field_aliases),
            description=description,
            fields=fields,
        )
        self.field_aliases = check.opt_dict_param(
            field_aliases, "field_aliases", key_type=str, value_type=str
        )
        self._initialized = True


class Map(ConfigType):
    """Defines a config dict with arbitrary scalar keys and typed values.

    A map can contrain arbitrary keys of the specified scalar type, each of which has
    type checked values. Unlike :py:class:`Shape` and :py:class:`Permissive`, scalar
    keys other than strings can be used, and unlike :py:class:`Permissive`, all
    values are type checked.

    Args:
        key_type (type):
            The type of keys this map can contain. Must be a scalar type.
        inner_type (type):
            The type of the values that this map type can contain.
        key_label_name (string):
            Optional name which describes the role of keys in the map.

    **Examples:**

    .. code-block:: python

        @op(config_schema=Field(Map({str: int})))
        def partially_specified_config(context) -> List:
            return sorted(list(context.op_config.items()))
    """

    def __init__(self, key_type, inner_type, key_label_name=None):
        from .field import resolve_to_config_type

        self.key_type = resolve_to_config_type(key_type)
        self.inner_type = resolve_to_config_type(inner_type)
        self.given_name = key_label_name

        check.inst_param(self.key_type, "key_type", ConfigType)
        check.inst_param(self.inner_type, "inner_type", ConfigType)
        check.param_invariant(
            self.key_type.kind == ConfigTypeKind.SCALAR, "key_type", "Key type must be a scalar"
        )
        check.opt_str_param(self.given_name, "name")

        super(Map, self).__init__(
            key="Map.{key_type}.{inner_type}{name_key}".format(
                key_type=self.key_type.key,
                inner_type=self.inner_type.key,
                name_key=f":name: {key_label_name}" if key_label_name else "",
            ),
            # We use the given name field to store the key label name
            # this is used elsewhere to give custom types names
            given_name=key_label_name,
            type_params=[self.key_type, self.inner_type],
            kind=ConfigTypeKind.MAP,
        )

    @public
    @property
    def key_label_name(self) -> Optional[str]:
        """Name which describes the role of keys in the map, if provided."""
        return self.given_name

    def type_iterator(self) -> Iterator["ConfigType"]:
        yield from self.key_type.type_iterator()
        yield from self.inner_type.type_iterator()
        yield from super().type_iterator()


def _define_permissive_dict_key(fields, description):
    return (
        "Permissive." + compute_fields_hash(fields, description=description)
        if fields
        else "Permissive"
    )


class Permissive(_ConfigHasFields):
    """Defines a config dict with a partially specified schema.

    A permissive dict allows partial specification of the config schema. Any fields with a
    specified schema will be type checked. Other fields will be allowed, but will be ignored by
    the type checker.

    Args:
        fields (Dict[str, Field]): The partial specification of the config dict.

    **Examples:**

    .. code-block:: python

        @op(config_schema=Field(Permissive({'required': Field(String)})))
        def map_config_op(context) -> List:
            return sorted(list(context.op_config.items()))
    """

    def __new__(cls, fields=None, description=None):
        return _memoize_inst_in_field_cache(
            cls,
            Permissive,
            _define_permissive_dict_key(
                expand_fields_dict(fields) if fields else None, description
            ),
        )

    def __init__(self, fields=None, description=None):
        # if we hit in field cache avoid double init
        if self._initialized:
            return

        fields = expand_fields_dict(fields) if fields else None
        super(Permissive, self).__init__(
            key=_define_permissive_dict_key(fields, description),
            kind=ConfigTypeKind.PERMISSIVE_SHAPE,
            fields=fields or dict(),
            description=description,
        )
        self._initialized = True


def _define_selector_key(fields, description):
    return "Selector." + compute_fields_hash(fields, description=description)


class Selector(_ConfigHasFields):
    """Define a config field requiring the user to select one option.

    Selectors are used when you want to be able to present several different options in config but
    allow only one to be selected. For example, a single input might be read in from either a csv
    file or a parquet file, but not both at once.

    Note that in some other type systems this might be called an 'input union'.

    Functionally, a selector is like a :py:class:`Dict`, except that only one key from the dict can
    be specified in valid config.

    Args:
        fields (Dict[str, Field]): The fields from which the user must select.

    **Examples:**

    .. code-block:: python

        @op(
            config_schema=Field(
                Selector(
                    {
                        'haw': {'whom': Field(String, default_value='honua', is_required=False)},
                        'cn': {'whom': Field(String, default_value='世界', is_required=False)},
                        'en': {'whom': Field(String, default_value='world', is_required=False)},
                    }
                ),
                is_required=False,
                default_value={'en': {'whom': 'world'}},
            )
        )
        def hello_world_with_default(context):
            if 'haw' in context.op_config:
                return 'Aloha {whom}!'.format(whom=context.op_config['haw']['whom'])
            if 'cn' in context.op_config:
                return '你好, {whom}!'.format(whom=context.op_config['cn']['whom'])
            if 'en' in context.op_config:
                return 'Hello, {whom}!'.format(whom=context.op_config['en']['whom'])
    """

    def __new__(cls, fields, description=None):
        return _memoize_inst_in_field_cache(
            cls,
            Selector,
            _define_selector_key(expand_fields_dict(fields), description),
        )

    def __init__(self, fields, description=None):
        # if we hit in field cache avoid double init
        if self._initialized:
            return

        fields = expand_fields_dict(fields)
        super(Selector, self).__init__(
            key=_define_selector_key(fields, description),
            kind=ConfigTypeKind.SELECTOR,
            fields=fields,
            description=description,
        )
        self._initialized = True


# Config syntax expansion code below


def is_potential_field(potential_field: object) -> bool:
    from .field import Field, resolve_to_config_type

    return isinstance(potential_field, (Field, dict, list)) or bool(
        resolve_to_config_type(potential_field)
    )


def convert_fields_to_dict_type(fields: Mapping[str, object]):
    return _convert_fields_to_dict_type(fields, fields, [])


def _convert_fields_to_dict_type(
    original_root: object, fields: Mapping[str, object], stack: List[str]
) -> Shape:
    return Shape(_expand_fields_dict(original_root, fields, stack))


def expand_fields_dict(fields: Mapping[str, object]) -> Mapping[str, "Field"]:
    return _expand_fields_dict(fields, fields, [])


def _expand_fields_dict(
    original_root: object, fields: Mapping[str, object], stack: List[str]
) -> Mapping[str, "Field"]:
    check.mapping_param(fields, "fields")
    return {
        name: _convert_potential_field(original_root, value, stack + [name])
        for name, value in fields.items()
    }


def expand_list(original_root: object, the_list: Sequence[object], stack: List[str]) -> Array:
    if len(the_list) != 1:
        raise DagsterInvalidConfigDefinitionError(
            original_root, the_list, stack, "List must be of length 1"
        )

    inner_type = _convert_potential_type(original_root, the_list[0], stack)
    if not inner_type:
        raise DagsterInvalidConfigDefinitionError(
            original_root,
            the_list,
            stack,
            "List have a single item and contain a valid type i.e. [int]. Got item {}".format(
                repr(the_list[0])
            ),
        )

    return Array(inner_type)


def expand_map(original_root: object, the_dict: Mapping[object, object], stack: List[str]) -> Map:
    if len(the_dict) != 1:
        raise DagsterInvalidConfigDefinitionError(
            original_root, the_dict, stack, "Map dict must be of length 1"
        )

    key = next(iter(the_dict.keys()))
    key_type = _convert_potential_type(original_root, key, stack)
    if not key_type or not key_type.kind == ConfigTypeKind.SCALAR:
        raise DagsterInvalidConfigDefinitionError(
            original_root,
            the_dict,
            stack,
            f"Map dict must have a scalar type as its only key. Got key {key!r}",
        )

    inner_type = _convert_potential_type(original_root, the_dict[key], stack)
    if not inner_type:
        raise DagsterInvalidConfigDefinitionError(
            original_root,
            the_dict,
            stack,
            "Map must have a single value and contain a valid type i.e. {{str: int}}. Got item {}"
            .format(repr(the_dict[key])),
        )

    return Map(key_type, inner_type)


def convert_potential_field(potential_field: object) -> "Field":
    return _convert_potential_field(potential_field, potential_field, [])


def _convert_potential_type(original_root: object, potential_type, stack: List[str]):
    from .field import resolve_to_config_type

    if isinstance(potential_type, Mapping):
        # A dictionary, containing a single key which is a type (int, str, etc) and not a string is interpreted as a Map
        if len(potential_type) == 1:
            key = next(iter(potential_type.keys()))
            if not isinstance(key, str) and _convert_potential_type(original_root, key, stack):
                return expand_map(original_root, potential_type, stack)

        # Otherwise, the dictionary is interpreted as a Shape
        return Shape(_expand_fields_dict(original_root, potential_type, stack))

    if isinstance(potential_type, list):
        return expand_list(original_root, potential_type, stack)

    return resolve_to_config_type(potential_type)


def _convert_potential_field(
    original_root: object, potential_field: object, stack: List[str]
) -> "Field":
    from .field import Field

    if potential_field is None:
        raise DagsterInvalidConfigDefinitionError(
            original_root, potential_field, stack, reason="Fields cannot be None"
        )

    if not is_potential_field(potential_field):
        raise DagsterInvalidConfigDefinitionError(original_root, potential_field, stack)

    if isinstance(potential_field, Field):
        return potential_field

    return Field(_convert_potential_type(original_root, potential_field, stack))


def config_dictionary_from_values(
    values: Mapping[str, Any], config_field: "Field"
) -> Dict[str, Any]:
    """Converts a set of config values into a dictionary representation,
    in particular converting EnvVar objects into Dagster config inputs
    and processing data structures such as dicts, lists, and structured Config classes.
    """
    assert ConfigTypeKind.is_shape(config_field.config_type.kind)

    from dagster._config.pythonic_config import _config_value_to_dict_representation

    return check.is_dict(_config_value_to_dict_representation(None, values))


def _create_direct_access_exception(cls: Type, env_var_name: str) -> Exception:
    return RuntimeError(
        f'Attempted to directly retrieve environment variable {cls.__name__}("{env_var_name}").'
        f" {cls.__name__} defers resolution of the environment variable value until run time, and"
        " should only be used as input to Dagster config or resources.\n\nTo access the"
        f" environment variable value, call `get_value` on the {cls.__name__}, or use os.getenv"
        " directly."
    )


class IntEnvVar(int):
    """Class used to represent an environment variable in the Dagster config system.

    The environment variable will be resolved to an int value when the config is
    loaded.
    """

    name: str

    @classmethod
    def create(cls, name: str) -> "IntEnvVar":
        var = IntEnvVar(0)
        var.name = name
        return var

    def __int__(self) -> int:
        """Raises an exception of the EnvVar value is directly accessed. Users should instead use
        the `get_value` method, or use the EnvVar as an input to Dagster config or resources.
        """
        raise _create_direct_access_exception(self.__class__, self.env_var_name)

    def __str__(self) -> str:
        return str(int(self))

    def get_value(self, default: Optional[int] = None) -> Optional[int]:
        """Returns the value of the environment variable, or the default value if the
        environment variable is not set. If no default is provided, None will be returned.
        """
        value = os.getenv(self.name, default=default)
        return int(value) if value else None

    @property
    def env_var_name(self) -> str:
        """Returns the name of the environment variable."""
        return self.name


class EnvVar(str):
    """Class used to represent an environment variable in the Dagster config system.

    This class is intended to be used to populate config fields or resources.
    The environment variable will be resolved to a string value when the config is
    loaded.

    To access the value of the environment variable, use the `get_value` method.
    """

    @classmethod
    def int(cls, name: str) -> "IntEnvVar":
        return IntEnvVar.create(name=name)

    def __str__(self) -> str:
        """Raises an exception of the EnvVar value is directly accessed. Users should instead use
        the `get_value` method, or use the EnvVar as an input to Dagster config or resources.
        """
        raise _create_direct_access_exception(self.__class__, self.env_var_name)

    @property
    def env_var_name(self) -> str:
        """Returns the name of the environment variable."""
        return super().__str__()

    def get_value(self, default: Optional[str] = None) -> Optional[str]:
        """Returns the value of the environment variable, or the default value if the
        environment variable is not set. If no default is provided, None will be returned.
        """
        return os.getenv(self.env_var_name, default=default)
