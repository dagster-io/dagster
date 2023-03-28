import typing
from enum import Enum as PythonEnum
from typing import TYPE_CHECKING, Dict, Iterator, Optional, Sequence, cast

import dagster._check as check
from dagster._annotations import public
from dagster._builtins import BuiltinEnum
from dagster._config import UserConfigSchema
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from .snap import ConfigSchemaSnapshot, ConfigTypeSnap


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


class ConfigType:
    """The class backing DagsterTypes as they are used processing configuration data."""

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

    @staticmethod
    def from_builtin_enum(builtin_enum: typing.Any) -> "ConfigType":
        check.invariant(BuiltinEnum.contains(builtin_enum), "param must be member of BuiltinEnum")
        return _CONFIG_MAP[builtin_enum]

    def post_process(self, value):
        """Implement this in order to take a value provided by the user
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

    def type_iterator(self) -> Iterator["ConfigType"]:
        yield self

    def get_schema_snapshot(self) -> "ConfigSchemaSnapshot":
        from .snap import ConfigSchemaSnapshot

        return ConfigSchemaSnapshot({ct.key: ct.get_snapshot() for ct in self.type_iterator()})


@whitelist_for_serdes
class ConfigScalarKind(PythonEnum):
    INT = "INT"
    STRING = "STRING"
    FLOAT = "FLOAT"
    BOOL = "BOOL"


# Scalars, Composites, Selectors, Lists, Optional, Any


class ConfigScalar(ConfigType):
    def __init__(
        self, key: str, given_name: Optional[str], scalar_kind: ConfigScalarKind, **kwargs: object
    ):
        self.scalar_kind = check.inst_param(scalar_kind, "scalar_kind", ConfigScalarKind)
        super(ConfigScalar, self).__init__(
            key, kind=ConfigTypeKind.SCALAR, given_name=given_name, **kwargs
        )


class BuiltinConfigScalar(ConfigScalar):
    def __init__(self, scalar_kind, description=None):
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
        from .field import resolve_to_config_type

        self.inner_type = cast(ConfigType, resolve_to_config_type(inner_type))
        super(Noneable, self).__init__(
            key=f"Noneable.{self.inner_type.key}",
            kind=ConfigTypeKind.NONEABLE,
            type_params=[self.inner_type],
        )

    def type_iterator(self) -> Iterator["ConfigType"]:
        yield from self.inner_type.type_iterator()
        yield from super().type_iterator()


class Array(ConfigType):
    """Defines an array (list) configuration type that contains values of type ``inner_type``.

    Args:
        inner_type (type):
            The type of the values that this configuration type can contain.
    """

    def __init__(self, inner_type: object):
        from .field import resolve_to_config_type

        self.inner_type = cast(ConfigType, resolve_to_config_type(inner_type))
        super(Array, self).__init__(
            key=f"Array.{self.inner_type.key}",
            type_params=[self.inner_type],
            kind=ConfigTypeKind.ARRAY,
        )

    @public
    @property
    def description(self):
        return f"List of {self.key}"

    def type_iterator(self) -> Iterator["ConfigType"]:
        yield from self.inner_type.type_iterator()
        yield from super().type_iterator()


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
                "Should never reach this. config_value should be pre-validated. Got {config_value}"
            ).format(config_value=value)
        )

    @classmethod
    def from_python_enum(cls, enum, name=None):
        """Create a Dagster enum corresponding to an existing Python enum.

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
        non_scalar_schema: UserConfigSchema,
        _key: Optional[str] = None,
    ):
        from .field import resolve_to_config_type

        self.scalar_type = check.inst(
            cast(ConfigType, resolve_to_config_type(scalar_type)), ConfigType
        )
        self.non_scalar_type = resolve_to_config_type(non_scalar_schema)

        check.param_invariant(self.scalar_type.kind == ConfigTypeKind.SCALAR, "scalar_type")
        check.param_invariant(
            self.non_scalar_type.kind
            in {ConfigTypeKind.STRICT_SHAPE, ConfigTypeKind.SELECTOR, ConfigTypeKind.ARRAY},
            "non_scalar_type",
        )

        # https://github.com/dagster-io/dagster/issues/2133
        key = check.opt_str_param(
            _key, "_key", f"ScalarUnion.{self.scalar_type.key}-{self.non_scalar_type.key}"
        )

        super(ScalarUnion, self).__init__(
            key=key,
            kind=ConfigTypeKind.SCALAR_UNION,
            type_params=[self.scalar_type, self.non_scalar_type],
        )

    def type_iterator(self) -> Iterator["ConfigType"]:
        yield from self.scalar_type.type_iterator()
        yield from self.non_scalar_type.type_iterator()
        yield from super().type_iterator()


ConfigAnyInstance: Any = Any()
ConfigBoolInstance: Bool = Bool()
ConfigFloatInstance: Float = Float()
ConfigIntInstance: Int = Int()
ConfigStringInstance: String = String()

_CONFIG_MAP: Dict[check.TypeOrTupleOfTypes, ConfigType] = {
    BuiltinEnum.ANY: ConfigAnyInstance,
    BuiltinEnum.BOOL: ConfigBoolInstance,
    BuiltinEnum.FLOAT: ConfigFloatInstance,
    BuiltinEnum.INT: ConfigIntInstance,
    BuiltinEnum.STRING: ConfigStringInstance,
}


_CONFIG_MAP_BY_NAME: Dict[str, ConfigType] = {
    "Any": ConfigAnyInstance,
    "Bool": ConfigBoolInstance,
    "Float": ConfigFloatInstance,
    "Int": ConfigIntInstance,
    "String": ConfigStringInstance,
}

ALL_CONFIG_BUILTINS = set(_CONFIG_MAP.values())


def get_builtin_scalar_by_name(type_name: str):
    if type_name not in _CONFIG_MAP_BY_NAME:
        check.failed(f"Scalar {type_name} is not supported")
    return _CONFIG_MAP_BY_NAME[type_name]
