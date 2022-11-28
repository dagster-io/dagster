from __future__ import annotations

import os
import typing
from enum import Enum as PythonEnum
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

from typing_extensions import Final, TypeAlias, TypeGuard

import dagster._check as check
from dagster._annotations import public
from dagster._builtins import BuiltinEnum
from dagster._config import ConfigSchema
from dagster._config.errors import PostProcessingError
from dagster._config.field import Field, hash_fields
from dagster._core.errors import (
    DagsterInvalidConfigDefinitionError,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
)
from dagster._serdes import whitelist_for_serdes
from dagster._utils.typing_api import is_closed_python_optional_type, is_typing_type

if TYPE_CHECKING:
    from .snap import ConfigSchemaSnap, ConfigTypeSnap

VALID_CONFIG_DESC: Final[
    str
] = """
1. A dagster config type: Int, Float, Bool, String, StringSource, Path, Any,
   Array, Noneable, Selector, Shape, Permissive, etc.

2. A Python primitive type. These resolve to their corresponding dagster config
   type: int -> Int, float -> Float, bool -> Bool, str -> String.

3. A bare python dictionary, which is wrapped in Shape. Any
   values in the dictionary get resolved by the same rules, recursively.

4. A bare python list of length one which itself is config type.
   Becomes Array with list element as an argument.

5. None. Becomes Any.
"""

CONFIG_SCHEMA_DESCRIPTION: Final[str] = """
A Dagster config schema is either a Field or an value coercible to a ConfigType.
"""

RawConfigType: TypeAlias = Union[
    "ConfigType",
    Type[Type[typing.Any]],
    Type[int],
    Type[float],
    Type[bool],
    Type[str],
    Type[list],
    Type[dict],
    Dict[object, object],
    List[object],
    None,
]

ConfigSchema: TypeAlias = Union[Field, RawConfigType]

# ########################
# ##### CONFIG TYPE KIND
# ########################

@whitelist_for_serdes
class ConfigTypeKind(PythonEnum):
    ANY = "ANY"
    SCALAR = "SCALAR"
    ENUM = "ENUM"

    SELECTOR = "SELECTOR"
    STRICT_SHAPE = "STRICT_SHAPE"
    PERMISSIVE_SHAPE = "PERMISSIVE_SHAPE"
    SCALAR_UNION = "SCALAR_UNION"

    MAP = "MAP"

    # Closed generic types
    ARRAY = "ARRAY"
    NONEABLE = "NONEABLE"

    @staticmethod
    def has_fields(kind: "ConfigTypeKind") -> bool:
        check.inst_param(kind, "kind", ConfigTypeKind)
        return kind == ConfigTypeKind.SELECTOR or ConfigTypeKind.is_shape(kind)

    @staticmethod
    def is_closed_generic(kind: "ConfigTypeKind") -> bool:
        check.inst_param(kind, "kind", ConfigTypeKind)
        return (
            kind == ConfigTypeKind.ARRAY
            or kind == ConfigTypeKind.NONEABLE
            or kind == ConfigTypeKind.SCALAR_UNION
            or kind == ConfigTypeKind.MAP
        )

    @staticmethod
    def is_shape(kind: "ConfigTypeKind") -> bool:
        check.inst_param(kind, "kind", ConfigTypeKind)
        return kind == ConfigTypeKind.STRICT_SHAPE or kind == ConfigTypeKind.PERMISSIVE_SHAPE

    @staticmethod
    def is_selector(kind: "ConfigTypeKind") -> bool:
        check.inst_param(kind, "kind", ConfigTypeKind)
        return kind == ConfigTypeKind.SELECTOR


HELPFUL_LIST_ERROR_STRING: Final[
    str
] = "Please use a python list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead."


def get_scalar_config_type_by_name(type_name: str) -> ConfigType:
    if type_name not in _NAME_TO_CONFIG_TYPE_MAP:
        check.failed("Scalar {} is not supported".format(type_name))
    return _NAME_TO_CONFIG_TYPE_MAP[type_name]


def is_valid_raw_config_type(obj: object) -> TypeGuard[RawConfigType]:
    try:
        normalize_config_type(obj)
    except DagsterInvalidDefinitionError:
        return False
    return True


def normalize_config_type(
    obj: object, root: Optional[object] = None, stack: Optional[List[str]] = None
) -> ConfigType:

    from .field import normalize_field

    root = root if root is not None else obj
    stack = stack if stack is not None else []

    if isinstance(obj, ConfigType):
        return obj

    # This also includes all "builtins" from `dagster._builtins`, which are just aliases for
    # Python types
    if obj in _PYTHON_TYPE_TO_CONFIG_TYPE_MAP:
        return _PYTHON_TYPE_TO_CONFIG_TYPE_MAP[obj]

    if obj is None:
        return ConfigAnyInstance

    # Length-1 dicts with a valid RawConfigType for a key are treated as Maps
    # Otherwise, keys must be strings and it is a Shape
    if isinstance(obj, dict):

        if all(isinstance(key, str) for key in obj.keys()):
            Shape({key: normalize_field(value, root, stack) for key, value in obj.items()})

        elif len(obj) == 1:
            key = next(iter(obj.keys()))
            try:
                key_type = normalize_config_type(key, root, stack)
                assert key_type.kind == ConfigTypeKind.SCALAR
            except (DagsterInvalidConfigDefinitionError, AssertionError):
                raise DagsterInvalidConfigDefinitionError(
                    root,
                    obj,
                    stack,
                    f"Map specification dict must have length of 1, with a scalar type for the key and an arbitrary type for the value, e.g. {{str: int}}. Invalid key type: {repr(key)}.",
                )

            try:
                value = obj[key]
                value_type = normalize_config_type(value, root, stack)
            except DagsterInvalidConfigDefinitionError:
                raise DagsterInvalidConfigDefinitionError(
                    root,
                    obj,
                    stack,
                    f"Map specification dict must have length of 1, with a scalar type for the key and an arbitrary type for the value, e.g. {{str: int}}. Invalid value type: {repr(obj[key])}.",
                )

            return Map(key_type, value_type)

    if isinstance(obj, list):
        if len(obj) != 1:
            raise DagsterInvalidConfigDefinitionError(
                root,
                obj,
                stack,
                "Array specification list must have a single element that is an arbitrary type, e.g. [int]. Invalid list has multiple items.",
            )

        try:
            element_type = normalize_config_type(obj[0], root, stack)
        except DagsterInvalidConfigDefinitionError:
            raise DagsterInvalidConfigDefinitionError(
                root,
                obj,
                stack,
                f"Array specification list must have a single element that is an arbitrary type, e.g. [int]. Invalid element_type: {repr(obj[0])}.",
            )
        return Array(element_type)

    # Special error messages for passing a DagsterType
    from dagster._core.types.dagster_type import DagsterType, List, ListType
    from dagster._core.types.python_set import Set, _TypedPythonSet
    from dagster._core.types.python_tuple import Tuple, _TypedPythonTuple

    if isinstance(obj, type) and issubclass(obj, ConfigType):
        raise DagsterInvalidConfigDefinitionError(
            root,
            obj,
            stack,
            f"Cannot pass config type class {obj} to normalize_config_type. "
            "This error usually occurs when you pass a dagster config type class instead of a class instance into "
            'another dagster config type. E.g. "Noneable(Permissive)" should instead be "Noneable(Permissive())".',
        )

    if isinstance(obj, type) and issubclass(obj, DagsterType):
        raise DagsterInvalidConfigDefinitionError(
            root,
            obj,
            stack,
            f"You have passed a DagsterType class {repr(obj)} to the config system. "
            "The DagsterType and config schema systems are separate. "
            f"Valid config values are:\n{VALID_CONFIG_DESC}",
        )

    if is_closed_python_optional_type(obj):
        raise DagsterInvalidConfigDefinitionError(
            root,
            obj,
            stack,
            "Cannot use typing.Optional as a config type. If you want this field to be "
            "optional, please use Field(<type>, is_required=False), and if you want this field to "
            "be required, but accept a value of None, use dagster.Noneable(<type>).",
        )

    if is_typing_type(obj):
        raise DagsterInvalidConfigDefinitionError(
            root,
            obj,
            stack,
            (
                f"You have passed in {obj} to the config system. Most types from "
                "the typing module in python are not allowed in the config system. "
                "You must use types that are imported from dagster or primitive types "
                "such as bool, int, etc."
            ),
        )

    if obj is List or isinstance(obj, ListType):
        raise DagsterInvalidConfigDefinitionError(
            root,
            obj,
            stack,
            "Cannot use List in the context of config. " + HELPFUL_LIST_ERROR_STRING,
        )

    if obj is Set or isinstance(obj, _TypedPythonSet):
        raise DagsterInvalidConfigDefinitionError(
            root,
            obj,
            stack,
            "Cannot use Set in the context of a config field. " + HELPFUL_LIST_ERROR_STRING,
        )

    if obj is Tuple or isinstance(obj, _TypedPythonTuple):
        raise DagsterInvalidConfigDefinitionError(
            root,
            obj,
            stack,
            "Cannot use Tuple in the context of a config field. " + HELPFUL_LIST_ERROR_STRING,
        )

    if isinstance(obj, DagsterType):
        raise DagsterInvalidConfigDefinitionError(
            root,
            obj,
            stack,
            (
                f"You have passed an instance of DagsterType {obj.display_name} to the config "
                f"system (Repr of type: {repr(obj)}). "
                "The DagsterType and config schema systems are separate. "
                f"Valid config values are:\n{VALID_CONFIG_DESC}"
            ),
        )

    raise DagsterInvalidConfigDefinitionError(
        root, obj, stack, f"Invalid value in config type specification: {obj}"
    )

# ########################
# ##### BASE CONFIG TYPE
# ########################

class ConfigType:
    """
    The class backing Dagster configuration types.
    """

    def __init__(
        self,
        key: str,
        kind: ConfigTypeKind,
        given_name: Optional[str] = None,
        description: Optional[str] = None,
        type_params: Optional[Sequence["ConfigType"]] = None,
    ):

        self.key: str = check.str_param(key, "key")
        self.kind: ConfigTypeKind = check.inst_param(kind, "kind", ConfigTypeKind)
        self.given_name: Optional[str] = check.opt_str_param(given_name, "given_name")
        self._description: Optional[str] = check.opt_str_param(description, "description")
        self.type_params: Optional[Sequence[ConfigType]] = (
            check.sequence_param(type_params, "type_params", of_type=ConfigType)
            if type_params
            else None
        )

        # memoized snap representation
        self._snap: Optional["ConfigTypeSnap"] = None

    @property
    def description(self) -> Optional[str]:
        return self._description

    def post_process(self, value: Any) -> Any:
        """
        Override this in order to take a value provided by the user
        and perform computation on it. This can be done to coerce data types,
        fetch things from the environment (e.g. environment variables), or
        to do custom validation. If the value is not valid, throw a
        PostProcessingError. Otherwise return the coerced value.
        """
        return value

    def get_snapshot(self) -> "ConfigTypeSnap":
        from .snap import snap_from_config_type

        if self._snap is None:
            self._snap = snap_from_config_type(self)

        return self._snap

    def descendant_type_iterator(self) -> Iterator["ConfigType"]:
        yield self

    def get_schema_snapshot(self) -> "ConfigSchemaSnap":
        """Generate a ConfigSchemaSnapshot containing a flat map of all the types at each descendant node of the tree."""
        from .snap import ConfigSchemaSnap

        return ConfigSchemaSnap({ct.key: ct.get_snapshot() for ct in self.descendant_type_iterator()})

    # override in subclasses that provide can provide an implicit default
    def has_implicit_default(self) -> bool:
        return False

# ########################
# ##### SCALAR CONFIG TYPES
# ########################


@whitelist_for_serdes
class ConfigScalarKind(PythonEnum):
    INT = "INT"
    STRING = "STRING"
    FLOAT = "FLOAT"
    BOOL = "BOOL"


class ConfigScalar(ConfigType):
    def __init__(
        self, key: str, given_name: Optional[str], scalar_kind: ConfigScalarKind, **kwargs: object
    ):
        self.scalar_kind = check.inst_param(scalar_kind, "scalar_kind", ConfigScalarKind)
        super(ConfigScalar, self).__init__(
            key, kind=ConfigTypeKind.SCALAR, given_name=given_name, **kwargs  # type: ignore
        )


class BuiltinConfigScalar(ConfigScalar):
    def __init__(self, scalar_kind: ConfigScalarKind, description: Optional[str]=None):
        super(BuiltinConfigScalar, self).__init__(
            key=type(self).__name__,
            given_name=type(self).__name__,
            scalar_kind=scalar_kind,
            description=description,
        )


class Int(BuiltinConfigScalar):
    def __init__(self):
        super(Int, self).__init__(scalar_kind=ConfigScalarKind.INT, description="")


class String(BuiltinConfigScalar):
    def __init__(self):
        super(String, self).__init__(scalar_kind=ConfigScalarKind.STRING, description="")


class Bool(BuiltinConfigScalar):
    def __init__(self):
        super(Bool, self).__init__(scalar_kind=ConfigScalarKind.BOOL, description="")


class Float(BuiltinConfigScalar):
    def __init__(self):
        super(Float, self).__init__(scalar_kind=ConfigScalarKind.FLOAT, description="")

    def post_process(self, value):
        return float(value)


class Any(ConfigType):
    def __init__(self):
        super(Any, self).__init__(
            key="Any",
            given_name="Any",
            kind=ConfigTypeKind.ANY,
        )


class Noneable(ConfigType):
    """Defines a configuration type that is the union of ``NoneType`` and the type ``inner_type``.

    Args:
        inner_type (type):
            The type of the values that this configuration type can contain.

    **Examples:**

    .. code-block:: python

       config_schema={"name": Noneable(str)}

       config={"name": "Hello"}  # Ok
       config={"name": None}     # Ok
       config={}                 # Error
    """

    def __init__(self, inner_type: object):

        self.inner_type = normalize_config_type(inner_type)
        super(Noneable, self).__init__(
            key=f"Noneable.{self.inner_type.key}",
            kind=ConfigTypeKind.NONEABLE,
            type_params=[self.inner_type],
        )

    def descendant_type_iterator(self) -> Iterator["ConfigType"]:
        yield from self.inner_type.descendant_type_iterator()
        yield from super().descendant_type_iterator()

    def has_implicit_default(self) -> bool:
        return True

# ########################
# ##### COLLECTION CONFIG TYPES
# ########################

class Array(ConfigType):
    """Defines an array (list) configuration type that contains values of type ``inner_type``.

    Args:
        inner_type (type):
            The type of the values that this configuration type can contain.
    """

    def __init__(self, inner_type: object):

        self.inner_type = normalize_config_type(inner_type)
        super(Array, self).__init__(
            key="Array.{inner_type}".format(inner_type=self.inner_type.key),
            type_params=[self.inner_type],
            kind=ConfigTypeKind.ARRAY,
        )

    @public  # type: ignore
    @property
    def description(self):
        return "List of {inner_type}".format(inner_type=self.key)

    def descendant_type_iterator(self) -> Iterator["ConfigType"]:
        yield from self.inner_type.descendant_type_iterator()
        yield from super().descendant_type_iterator()


class EnumValue:
    """Define an entry in a :py:class:`Enum`.

    Args:
        config_value (str):
            The string representation of the config to accept when passed.
        python_value (Optional[Any]):
            The python value to convert the enum entry in to. Defaults to the ``config_value``.
        description (Optional[str]):
            A human-readable description of the enum entry.

    """

    def __init__(
        self,
        config_value: str,
        python_value: Optional[object] = None,
        description: Optional[str] = None,
    ):
        self.config_value = check.str_param(config_value, "config_value")
        self.python_value = config_value if python_value is None else python_value
        self.description = check.opt_str_param(description, "description")


class Enum(ConfigType):
    """Defines a enum configuration type that allows one of a defined set of possible values.

    Args:
        name (str):
            The name of the enum configuration type.
        enum_values (List[EnumValue]):
            The set of possible values for the enum configuration type.

    **Examples:**

    .. code-block:: python

        @op(
            config_schema=Field(
                Enum(
                    'CowboyType',
                    [
                        EnumValue('good'),
                        EnumValue('bad'),
                        EnumValue('ugly'),
                    ]
                )
            )
        )
        def resolve_standoff(context):
            # ...
    """

    def __init__(self, name: str, enum_values: Sequence[EnumValue]):
        check.str_param(name, "name")
        super(Enum, self).__init__(key=name, given_name=name, kind=ConfigTypeKind.ENUM)
        self.enum_values = check.sequence_param(enum_values, "enum_values", of_type=EnumValue)
        self._valid_python_values = {ev.python_value for ev in enum_values}
        check.invariant(len(self._valid_python_values) == len(enum_values))
        self._valid_config_values = {ev.config_value for ev in enum_values}
        check.invariant(len(self._valid_config_values) == len(enum_values))

    @property
    def config_values(self):
        return [ev.config_value for ev in self.enum_values]

    def is_valid_config_enum_value(self, config_value):
        return config_value in self._valid_config_values

    def post_process(self, value: typing.Any) -> typing.Any:
        if isinstance(value, PythonEnum):
            value = value.name

        for ev in self.enum_values:
            if ev.config_value == value:
                return ev.python_value

        check.failed(
            (
                "Should never reach this. config_value should be pre-validated. "
                "Got {config_value}"
            ).format(config_value=value)
        )

    @classmethod
    def from_python_enum(cls, enum, name=None):
        """
        Create a Dagster enum corresponding to an existing Python enum.

        Args:
            enum (enum.EnumMeta):
                The class representing the enum.
            name (Optional[str]):
                The name for the enum. If not present, `enum.__name__` will be used.

        Example:

        .. code-block:: python

            class Color(enum.Enum):
                RED = enum.auto()
                GREEN = enum.auto()
                BLUE = enum.auto()

            @op(
                config_schema={"color": Field(Enum.from_python_enum(Color))}
            )
            def select_color(context):
                # ...
        """
        if name is None:
            name = enum.__name__
        return cls(name, [EnumValue(v.name, python_value=v) for v in enum])

# ########################
# ##### SCALAR UNION CONFIG TYPES
# ########################

class ScalarUnion(ConfigType):
    """Defines a configuration type that accepts a scalar value OR a non-scalar value like a
    :py:class:`~dagster.List`, :py:class:`~dagster.Dict`, or :py:class:`~dagster.Selector`.

    This allows runtime scalars to be configured without a dictionary with the key ``value`` and
    instead just use the scalar value directly. However this still leaves the option to
    load scalars from a json or pickle file.

    Args:
        scalar_type (type):
            The scalar type of values that this configuration type can hold. For example,
            :py:class:`~python:int`, :py:class:`~python:float`, :py:class:`~python:bool`,
            or :py:class:`~python:str`.
        non_scalar_schema (ConfigSchema):
            The schema of a non-scalar Dagster configuration type. For example, :py:class:`List`,
            :py:class:`Dict`, or :py:class:`~dagster.Selector`.
        key (Optional[str]):
            The configuation type's unique key. If not set, then the key will be set to
            ``ScalarUnion.{scalar_type}-{non_scalar_schema}``.

    **Examples:**

    .. code-block:: yaml

        graph:
          transform_word:
            inputs:
              word:
                value: foobar


    becomes, optionally,


    .. code-block:: yaml

        graph:
          transform_word:
            inputs:
              word: foobar
    """

    def __init__(
        self,
        scalar_type: typing.Any,
        non_scalar_schema: ConfigSchema,
        _key: Optional[str] = None,
    ):

        self.scalar_type = normalize_config_type(scalar_type)
        self.non_scalar_type = normalize_config_type(non_scalar_schema)

        check.param_invariant(self.scalar_type.kind == ConfigTypeKind.SCALAR, "scalar_type")
        check.param_invariant(
            self.non_scalar_type.kind
            in {ConfigTypeKind.STRICT_SHAPE, ConfigTypeKind.SELECTOR, ConfigTypeKind.ARRAY},
            "non_scalar_type",
        )

        # https://github.com/dagster-io/dagster/issues/2133
        key = check.opt_str_param(
            _key, "_key", "ScalarUnion.{}-{}".format(self.scalar_type.key, self.non_scalar_type.key)
        )

        super(ScalarUnion, self).__init__(
            key=key,
            kind=ConfigTypeKind.SCALAR_UNION,
            type_params=[self.scalar_type, self.non_scalar_type],
        )

    def descendant_type_iterator(self) -> Iterator["ConfigType"]:
        yield from self.scalar_type.descendant_type_iterator()
        yield from self.non_scalar_type.descendant_type_iterator()
        yield from super().descendant_type_iterator()

_VALID_STRING_SOURCE_TYPES: Final[Tuple[Type[typing.Any], ...]] = (str, dict)

def _fetch_env_variable(var: str) -> str:
    check.str_param(var, "var")
    value = os.getenv(var)
    if value is None:
        raise PostProcessingError(
            (
                'You have attempted to fetch the environment variable "{var}" '
                "which is not set. In order for this execution to succeed it "
                "must be set in this environment."
            ).format(var=var)
        )
    return value

class StringSourceType(ScalarUnion):
    def __init__(self):
        super(StringSourceType, self).__init__(
            scalar_type=str,
            non_scalar_schema=Selector({"env": str}),
            _key="StringSourceType",
        )

    def post_process(self, value):
        check.param_invariant(isinstance(value, _VALID_STRING_SOURCE_TYPES), "value")

        if not isinstance(value, dict):
            return value

        key, cfg = list(value.items())[0]
        check.invariant(key == "env", "Only valid key is env")
        return str(_fetch_env_variable(cfg))


class IntSourceType(ScalarUnion):
    def __init__(self):
        super(IntSourceType, self).__init__(
            scalar_type=int,
            non_scalar_schema=Selector({"env": str}),
            _key="IntSourceType",
        )

    def post_process(self, value):
        check.param_invariant(isinstance(value, (dict, int)), "value", "Should be pre-validated")

        if not isinstance(value, dict):
            return value

        check.invariant(len(value) == 1, "Selector should have one entry")

        key, cfg = list(value.items())[0]
        check.invariant(key == "env", "Only valid key is env")
        value = _fetch_env_variable(cfg)
        try:
            return int(value)
        except ValueError as e:
            raise PostProcessingError(
                (
                    'Value "{value}" stored in env variable "{var}" cannot be '
                    "coerced into an int."
                ).format(value=value, var=cfg)
            ) from e


class BoolSourceType(ScalarUnion):
    def __init__(self):
        super(BoolSourceType, self).__init__(
            scalar_type=bool,
            non_scalar_schema=Selector({"env": str}),
            _key="BoolSourceType",
        )

    def post_process(self, value):
        check.param_invariant(isinstance(value, (dict, bool)), "value", "Should be pre-validated")

        if not isinstance(value, dict):
            return value

        check.invariant(len(value) == 1, "Selector should have one entry")

        key, cfg = list(value.items())[0]
        check.invariant(key == "env", "Only valid key is env")
        value = _fetch_env_variable(cfg)
        try:
            return bool(value)
        except ValueError as e:
            raise PostProcessingError(
                (
                    'Value "{value}" stored in env variable "{var}" cannot be '
                    "coerced into an bool."
                ).format(value=value, var=cfg)
            ) from e



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

        self.key_type = normalize_config_type(key_type)
        self.inner_type = normalize_config_type(inner_type)
        self.given_name = key_label_name

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

    @public  # type: ignore
    @property
    def key_label_name(self):
        return self.given_name

    def descendant_type_iterator(self) -> Iterator["ConfigType"]:
        yield from self.key_type.descendant_type_iterator()
        yield from self.inner_type.descendant_type_iterator()
        yield from super().descendant_type_iterator()

_MEMOIZED_CONFIG_TYPES: Final[Dict[str, KeyValueConfigType]] = {}

class KeyValueConfigType(ConfigType):

    @classmethod
    def get_memoized_instance(cls, key: str):
        if not key in _MEMOIZED_CONFIG_TYPES:
            _MEMOIZED_CONFIG_TYPES[key] = super(cls, cls).__new__(cls)
        return _MEMOIZED_CONFIG_TYPES[key]

    @classmethod
    def get_key(
        cls,
        fields: Optional[Mapping[str, object]] = None,
        description: Optional[str] = None,
        field_aliases: Optional[Mapping[str, str]] = None,
    ) -> str:
        return (
            ".".join([cls.__name__, hash_fields(fields, description, field_aliases)])
            if fields is not None
            else cls.__name__
        )

    _is_initialized: bool = False

    def __init__(self, fields: Mapping[str, object], **kwargs):
        from .field import normalize_field
        self.fields = {key: normalize_field(value) for key, value in fields.items()}
        super(KeyValueConfigType, self).__init__(**kwargs)

    def descendant_type_iterator(self) -> Iterator["ConfigType"]:
        for field in self.fields.values():
            yield from field.config_type.descendant_type_iterator()
        yield from super().descendant_type_iterator()

class Shape(KeyValueConfigType):
    """Schema for configuration data with string keys and typed values via :py:class:`Field`.

    Unlike :py:class:`Permissive`, unspecified fields are not allowed and will throw a
    :py:class:`~dagster.DagsterInvalidConfigError`.

    Args:
        fields (Dict[str, Field]):
            The specification of the config dict.
        field_aliases (Dict[str, str]):
            Maps a string key to an alias that can be used instead of the original key. For example,
            an entry {"solids": "ops"} means that someone could use "ops" instead of "solids" as a
            top level string key.
    """

    def __new__(
        cls,
        fields: Mapping[str, object],
        description: Optional[str] = None,
        field_aliases: Optional[Mapping[str, str]] = None,
    ):
        key = cls.get_key(fields, description, field_aliases)
        return cls.get_memoized_instance(key)

    def __init__(
        self,
        fields: Mapping[str, object],
        description: Optional[str] = None,
        field_aliases: Optional[Mapping[str, str]] = None,
    ):
        # if we hit in the field cache - skip double init
        if self._is_initialized:
            return

        fields = expand_fields_dict(fields)
        super(Shape, self).__init__(
            kind=ConfigTypeKind.STRICT_SHAPE,
            key=Shape.get_key(fields, description, field_aliases),
            description=description,
            fields=fields,
        )
        self.field_aliases = check.opt_dict_param(
            field_aliases, "field_aliases", key_type=str, value_type=str
        )
        self._is_initialized = True

    def has_implicit_default(self) -> bool:
        for field in self.fields.values():
            if field.is_required:
                return False
        return True


class Permissive(KeyValueConfigType):
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

    def __new__(
        cls,
        fields: Optional[Mapping[str, object]] = None,
        description: Optional[str] = None,
    ):
        key = cls.get_key(fields, description)
        return cls.get_memoized_instance(key)

    def __init__(
        self,
        fields: Optional[Mapping[str, object]] = None,
        description: Optional[str] = None,
    ):
        # if we hit in field cache avoid double init
        if self._is_initialized:
            return

        super(Permissive, self).__init__(
            key=Permissive.get_key(fields, description),
            kind=ConfigTypeKind.PERMISSIVE_SHAPE,
            fields=fields or dict(),
            description=description,
        )
        self._is_initialized = True

    def has_implicit_default(self) -> bool:
        for field in self.fields.values():
            if field.is_required:
                return False
        return True


class Selector(KeyValueConfigType):
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
                return '你好，{whom}!'.format(whom=context.op_config['cn']['whom'])
            if 'en' in context.op_config:
                return 'Hello, {whom}!'.format(whom=context.op_config['en']['whom'])
    """

    def __new__(
        cls,
        fields: Optional[Mapping[str, object]] = None,
        description: Optional[str] = None,
    ):
        key = cls.get_key(fields, description)
        return cls.get_memoized_instance(key)

    def __init__(
        self,
        fields: Optional[Mapping[str, object]] = None,
        description: Optional[str] = None,
    ):
        if self._is_initialized:
            return

        super(Selector, self).__init__(
            key=Selector.get_key(fields, description),
            kind=ConfigTypeKind.SELECTOR,
            fields=fields or dict(),
            description=description,
        )
        self._is_initialized = True

    def has_implicit_default(self) -> bool:
        if len(config_type.fields) == 1:  # type: ignore
            for field in config_type.fields.values():  # type: ignore
                if field.is_required:
                    return False
            return True
        else:
            return False

ConfigAnyInstance: Any = Any()
ConfigBoolInstance: Bool = Bool()
ConfigFloatInstance: Float = Float()
ConfigIntInstance: Int = Int()
ConfigStringInstance: String = String()

StringSource: StringSourceType = StringSourceType()
IntSource: IntSourceType = IntSourceType()
BoolSource: BoolSourceType = BoolSourceType()

_PYTHON_TYPE_TO_CONFIG_TYPE_MAP: Final[Dict[Type[object], ConfigType]] = {
    typing.Any: ConfigAnyInstance,
    bool: ConfigBoolInstance,
    float: ConfigFloatInstance,
    int: ConfigIntInstance,
    str: ConfigStringInstance,
    list: Array(ConfigAnyInstance),
    dict: Permissive(),
}


_NAME_TO_CONFIG_TYPE_MAP: Dict[str, ConfigType] = {
    "Any": ConfigAnyInstance,
    "Bool": ConfigBoolInstance,
    "Float": ConfigFloatInstance,
    "Int": ConfigIntInstance,
    "String": ConfigStringInstance,
}

ALL_CONFIG_BUILTINS = set(_CONFIG_MAP.values())
