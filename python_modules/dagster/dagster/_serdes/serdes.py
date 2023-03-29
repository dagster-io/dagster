"""Serialization & deserialization for Dagster objects.

Why have custom serialization?

* Default json serialization doesn't work well on namedtuples, which we use extensively to create
  immutable value types. Namedtuples serialize like tuples as flat lists.
* Explicit whitelisting should help ensure we are only persisting or communicating across a
  serialization boundary the types we expect to.

Why not pickle?

* This isn't meant to replace pickle in the conditions that pickle is reasonable to use
  (in memory, not human readable, etc) just handle the json case effectively.
"""

import collections.abc
import warnings
from abc import ABC, abstractmethod
from enum import Enum
from inspect import Parameter, signature
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    FrozenSet,
    Generic,
    List,
    Mapping,
    NamedTuple,
    NoReturn,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
    overload,
)

from typing_extensions import Final, Literal, Self, TypeAlias, TypeGuard, TypeVar

import dagster._check as check
import dagster._seven as seven
from dagster._utils import is_named_tuple_instance, is_named_tuple_subclass
from dagster._utils.cached_method import cached_method

from .errors import DeserializationError, SerdesUsageError, SerializationError

###################################################################################################
# Types
###################################################################################################

JsonSerializableValue: TypeAlias = Union[
    Sequence["JsonSerializableValue"],
    Mapping[str, "JsonSerializableValue"],
    str,
    int,
    float,
    bool,
    None,
]

PackableValue: TypeAlias = Union[
    Sequence["PackableValue"],
    Mapping[str, "PackableValue"],
    str,
    int,
    float,
    bool,
    None,
    NamedTuple,
    Set["PackableValue"],
    FrozenSet["PackableValue"],
    Enum,
]


###################################################################################################
# Whitelisting
###################################################################################################


class WhitelistMap(NamedTuple):
    tuples: Dict[str, "NamedTupleSerializer"]
    enums: Dict[str, "EnumSerializer"]

    def register_tuple(
        self,
        name: str,
        named_tuple_class: Type[NamedTuple],
        serializer_class: Optional[Type["NamedTupleSerializer"]] = None,
        storage_name: Optional[str] = None,
        old_storage_names: Optional[AbstractSet[str]] = None,
        storage_field_names: Optional[Mapping[str, str]] = None,
        old_fields: Optional[Mapping[str, JsonSerializableValue]] = None,
        skip_when_empty_fields: Optional[AbstractSet[str]] = None,
        field_serializers: Optional[Mapping[str, Type["FieldSerializer"]]] = None,
    ):
        """Register a tuple in the whitelist map.

        Args:
            name: The class name of the namedtuple to register
            nt: The namedtuple class to register.
                Can be None to gracefull load previously serialized objects as None.
            serializer: The class to use when serializing and deserializing
        """
        serializer_class = serializer_class or NamedTupleSerializer
        serializer = serializer_class(
            klass=named_tuple_class,
            storage_name=storage_name,
            storage_field_names=storage_field_names,
            old_fields=old_fields,
            skip_when_empty_fields=skip_when_empty_fields,
            field_serializers={k: klass.get_instance() for k, klass in field_serializers.items()}
            if field_serializers
            else None,
        )
        self.tuples[name] = serializer
        if storage_name:
            self.tuples[storage_name] = serializer
        if old_storage_names:
            for old_storage_name in old_storage_names:
                self.tuples[old_storage_name] = serializer

    def has_tuple_entry(self, name: str) -> bool:
        return name in self.tuples

    def get_tuple_entry(self, name: str) -> "NamedTupleSerializer":
        return self.tuples[name]

    def register_enum(
        self,
        name: str,
        enum_class: Type[Enum],
        serializer_class: Optional[Type["EnumSerializer"]] = None,
        storage_name: Optional[str] = None,
        old_storage_names: Optional[AbstractSet[str]] = None,
    ) -> None:
        serializer_class = serializer_class or EnumSerializer
        serializer = serializer_class(
            klass=enum_class,
            storage_name=storage_name,
        )
        self.enums[name] = serializer
        if storage_name:
            self.enums[storage_name] = serializer
        if old_storage_names:
            for old_storage_name in old_storage_names:
                self.enums[old_storage_name] = serializer

    def has_enum_entry(self, name: str) -> bool:
        return name in self.enums

    def get_enum_entry(self, name: str) -> "EnumSerializer":
        return self.enums[name]

    @staticmethod
    def create() -> "WhitelistMap":
        return WhitelistMap(tuples={}, enums={})


_WHITELIST_MAP: Final[WhitelistMap] = WhitelistMap.create()

T = TypeVar("T")
U = TypeVar("U")
T_Type = TypeVar("T_Type", bound=Type[object])
T_Scalar = TypeVar("T_Scalar", bound=Union[str, int, float, bool, None])


@overload
def whitelist_for_serdes(__cls: T_Type) -> T_Type:
    ...


@overload
def whitelist_for_serdes(
    __cls: None = None,
    *,
    serializer: Optional[Type["Serializer"]] = ...,
    storage_name: Optional[str] = ...,
    old_storage_names: Optional[AbstractSet[str]] = None,
    storage_field_names: Optional[Mapping[str, str]] = ...,
    old_fields: Optional[Mapping[str, JsonSerializableValue]] = ...,
    skip_when_empty_fields: Optional[AbstractSet[str]] = ...,
    field_serializers: Optional[Mapping[str, Type["FieldSerializer"]]] = None,
) -> Callable[[T_Type], T_Type]:
    ...


def whitelist_for_serdes(
    __cls: Optional[T_Type] = None,
    *,
    serializer: Optional[Type["Serializer"]] = None,
    storage_name: Optional[str] = None,
    old_storage_names: Optional[AbstractSet[str]] = None,
    storage_field_names: Optional[Mapping[str, str]] = None,
    old_fields: Optional[Mapping[str, JsonSerializableValue]] = None,
    skip_when_empty_fields: Optional[AbstractSet[str]] = None,
    field_serializers: Optional[Mapping[str, Type["FieldSerializer"]]] = None,
) -> Union[T_Type, Callable[[T_Type], T_Type]]:
    """Decorator to whitelist a NamedTuple or Enum subclass to be serializable. Various arguments can be passed
    to alter serialization behavior for backcompat purposes.

    Args:
      serializer (Type[Serializer]):
          A custom serializer class to use. For NamedTuples, should inherit from
          `NamedTupleSerializer` and use any of hooks `before_unpack`, `after_pack`, and
          `handle_unpack_error`. For Enums, should inherit from `EnumSerializer` and use any of hooks
          `pack` or `unpack`.
      storage_name (Optional[str]):
          A string that will replace the class name when serializing and deserializing. For example,
          if `StorageFoo` is set as the `storage_name` for `Foo`, then `Foo` will be serialized with
          `"__class__": "StorageFoo"`, and dicts encountered with `"__class__": "StorageFoo"` during
          deserialization will be handled by the `Foo` serializer.
      old_storage_names (Optional[AbstractSet[str]]):
          A set of strings that act as aliases for the target class when deserializing. For example,
          if `OldFoo` is is passed as an old storage name for `Foo`, then dicts encountered with
          `"__class__": "OldFoo"` during deserialization will be handled by the `Foo` serializer.
      storage_field_names (Optional[Mapping[str, str]]):
          A mapping of field names to the names used during serializing and deserializing. For
          example, if `{"bar": "baz"}` is passed as `storage_field_names` for `Foo`, then
          serializing `Foo(bar=1)` will give `{"__class__": "Foo", "baz": 1}`, and deserializing
          this dict will give `Foo(bar=1)`. Only applies to NamedTuples.
      old_fields (Optional[Mapping[str, JsonSerializableValue]]):
         A mapping of old field names to default values that will be assigned on serialization. This
         is useful for providing backwards compatibility for fields that have been deleted. For
         example, if `{"bar": None}` is passed as `old_fields` for Foo (which has no defined `bar`
         field), then serializing `Foo(...)` will give `{"__class__": "Foo", "bar": None, ...}`.
         Only applies to NamedTuples.
      skip_when_empty_fields (Optional[AbstractSet[str]]):
          A set of fields that should be skipped when serializing if they are an empty collection
          (list, dict, tuple, or set). This allows a stable snapshot ID to be maintained when a new
          field is added. For example, if `{"bar"}` is passed as `skip_when_empty_fields` for `Foo`,
          then serializing `Foo(bar=[])` will give `{"__class__": "Foo"}` (no `bar` in the
          serialization). This is because the `[]` is an empty list and so is dropped. Only applies
          to NamedTuples.
      field_serializers (Optional[Mapping[str, FieldSerializer]]):
          A mapping of field names to `FieldSerializer` classes containing custom serialization
          logic. If a field has an associated `FieldSerializer`, then the `pack` and `unpack`
          methods on the `FieldSerializer` will be used instead of defaults. This is mostly useful
          for data structures that are broadly used throughout the codebase but change format.
          The canonical example is `MetadataFieldSerializer`.  Note that if the field needs to be
          stored under a different name, then it still needs an entry in `storage_field_names` even
          if a `FieldSerializer` is provided. Only applies to NamedTuples.
    """
    if storage_field_names or old_fields or skip_when_empty_fields:
        check.invariant(
            serializer is None or issubclass(serializer, NamedTupleSerializer),
            (
                "storage_field_names, old_fields, skip_when_empty_fields can only be used with a"
                " NamedTupleSerializer"
            ),
        )
    if __cls is not None:  # decorator invoked directly on class
        check.class_param(__cls, "__cls")
        return _whitelist_for_serdes(whitelist_map=_WHITELIST_MAP)(__cls)
    else:  # decorator passed params
        check.opt_class_param(serializer, "serializer", superclass=Serializer)
        return _whitelist_for_serdes(
            whitelist_map=_WHITELIST_MAP,
            serializer=serializer,
            storage_name=storage_name,
            old_storage_names=old_storage_names,
            storage_field_names=storage_field_names,
            old_fields=old_fields,
            skip_when_empty_fields=skip_when_empty_fields,
            field_serializers=field_serializers,
        )


def _whitelist_for_serdes(
    whitelist_map: WhitelistMap,
    serializer: Optional[Type["Serializer"]] = None,
    storage_name: Optional[str] = None,
    old_storage_names: Optional[AbstractSet[str]] = None,
    storage_field_names: Optional[Mapping[str, str]] = None,
    old_fields: Optional[Mapping[str, JsonSerializableValue]] = None,
    skip_when_empty_fields: Optional[AbstractSet[str]] = None,
    field_serializers: Optional[Mapping[str, Type["FieldSerializer"]]] = None,
) -> Callable[[T_Type], T_Type]:
    def __whitelist_for_serdes(klass: T_Type) -> T_Type:
        if issubclass(klass, Enum) and (
            serializer is None or issubclass(serializer, EnumSerializer)
        ):
            whitelist_map.register_enum(
                klass.__name__,
                klass,
                serializer,
                storage_name=storage_name,
                old_storage_names=old_storage_names,
            )
            return klass
        elif is_named_tuple_subclass(klass) and (
            serializer is None or issubclass(serializer, NamedTupleSerializer)
        ):
            _check_serdes_tuple_class_invariants(klass)
            whitelist_map.register_tuple(
                klass.__name__,
                klass,
                serializer,
                storage_name=storage_name,
                old_storage_names=old_storage_names,
                storage_field_names=storage_field_names,
                old_fields=old_fields,
                skip_when_empty_fields=skip_when_empty_fields,
                field_serializers=field_serializers,
            )
            return klass  # type: ignore  # (NamedTuple quirk)
        else:
            raise SerdesUsageError(f"Can not whitelist class {klass} for serializer {serializer}")

    return __whitelist_for_serdes


class Serializer(ABC):
    pass


T_Enum = TypeVar("T_Enum", bound=Enum, default=Enum)


class EnumSerializer(Serializer, Generic[T_Enum]):
    def __init__(self, *, klass: Type[T_Enum], storage_name: Optional[str] = None):
        self.klass = klass
        self.storage_name = storage_name

    def unpack(self, value: str) -> T_Enum:
        return self.klass[value]

    def pack(self, value: Enum, whitelist_map: WhitelistMap, descent_path: str) -> str:
        return f"{self.get_storage_name()}.{value.name}"

    def get_storage_name(self) -> str:
        return self.storage_name or self.klass.__name__


T_NamedTuple = TypeVar("T_NamedTuple", bound=NamedTuple, default=NamedTuple)

EMPTY_VALUES_TO_SKIP: Tuple[None, List[Any], Dict[Any, Any], Set[Any]] = (None, [], {}, set())


class NamedTupleSerializer(Serializer, Generic[T_NamedTuple]):
    # NOTE: See `whitelist_for_serdes` docstring for explanations of parameters.
    def __init__(
        self,
        *,
        klass: Type[T_NamedTuple],
        storage_name: Optional[str] = None,
        storage_field_names: Optional[Mapping[str, str]] = None,
        old_fields: Optional[Mapping[str, JsonSerializableValue]] = None,
        skip_when_empty_fields: Optional[AbstractSet[str]] = None,
        field_serializers: Optional[Mapping[str, "FieldSerializer"]] = None,
    ):
        self.klass = klass
        self.storage_name = storage_name
        self.storage_field_names = storage_field_names or {}
        self.old_fields = old_fields or {}
        self.skip_when_empty_fields = skip_when_empty_fields or set()
        self.field_serializers = field_serializers or {}

    def unpack(
        self,
        storage_dict: Dict[str, Any],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> T_NamedTuple:
        try:
            storage_dict = self.before_unpack(**storage_dict)
            unpacked: Dict[str, PackableValue] = {}
            for key, value in storage_dict.items():
                loaded_name = self.get_loaded_field_name(field=key)
                # Naively implements backwards compatibility by filtering arguments that aren't present in
                # the constructor. If a property is present in the serialized object, but doesn't exist in
                # the version of the class loaded into memory, that property will be completely ignored.
                if loaded_name in self.constructor_param_names:
                    unpack_fn = self.get_field_unpack_fn(field=loaded_name)
                    unpacked[loaded_name] = unpack_fn(
                        value, whitelist_map=whitelist_map, descent_path=descent_path
                    )

            # False positive type error here due to an eccentricity of `NamedTuple`-- calling `NamedTuple`
            # directly acts as a class factory, which is not true for `NamedTuple` subclasses (which act
            # like normal constructors). Because we have no subclass info here, the type checker thinks
            # we are invoking the class factory and complains about arguments.
            return self.klass(**unpacked)  # type: ignore
        except Exception as exc:
            return self.handle_unpack_error(exc, **storage_dict)

    # Hook: Modify the contents of the loaded dict before it is unpacked into domain objects during
    # deserialization.
    def before_unpack(self, **raw_dict: JsonSerializableValue) -> Dict[str, JsonSerializableValue]:
        return raw_dict

    # Hook: Handle an error that occurs when unpacking a NamedTuple. Can be used to return a default
    # value.
    def handle_unpack_error(self, exc: Exception, **storage_dict: Any) -> NoReturn:
        raise exc

    def pack(
        self,
        value: T_NamedTuple,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Dict[str, JsonSerializableValue]:
        packed: Dict[str, JsonSerializableValue] = {}
        packed["__class__"] = self.get_storage_name()
        for key, inner_value in value._asdict().items():
            if key in self.skip_when_empty_fields and inner_value in EMPTY_VALUES_TO_SKIP:
                continue
            storage_key = self.get_storage_field_name(field=key)
            pack_fn = self.get_field_pack_fn(field=key)
            packed[storage_key] = pack_fn(
                inner_value, whitelist_map=whitelist_map, descent_path=f"{descent_path}.{key}"
            )
        for key, default in self.old_fields.items():
            packed[key] = default
        packed = self.after_pack(**packed)
        return packed

    # Hook: Modify the contents of the packed, json-serializable dict before it is converted to a
    # string.
    def after_pack(self, **packed_dict: JsonSerializableValue) -> Dict[str, JsonSerializableValue]:
        return packed_dict

    @property
    @cached_method
    def constructor_param_names(self) -> Sequence[str]:
        return list(signature(self.klass.__new__).parameters.keys())

    def get_storage_name(self) -> str:
        return self.storage_name or self.klass.__name__

    def get_field_unpack_fn(self, field: str) -> Callable[..., PackableValue]:
        field_serializer = self.field_serializers.get(field)
        return field_serializer.unpack if field_serializer else unpack_value

    def get_field_pack_fn(self, field: str) -> Callable[..., JsonSerializableValue]:
        field_serializer = self.field_serializers.get(field)
        return field_serializer.pack if field_serializer else pack_value

    @cached_method
    def get_storage_field_name(self, field: str) -> str:
        return self.storage_field_names.get(field, field)

    @cached_method
    def get_loaded_field_name(self, field: str) -> str:
        for k, v in self.storage_field_names.items():
            if v == field:
                return k
        return field


class FieldSerializer(Serializer):
    _instance = None

    # Because `FieldSerializer` is not currently parameterizable (all variation is contained in the
    # logic of pack/unpack), we store references to a singleton instance in the whitelist map to
    # save memory.
    @classmethod
    def get_instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @abstractmethod
    def unpack(
        self,
        __packed_value: Any,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> PackableValue:
        ...

    @abstractmethod
    def pack(
        self,
        __unpacked_value: Any,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue:
        ...


###################################################################################################
# Serialize / Pack
###################################################################################################


def serialize_value(
    val: PackableValue, whitelist_map: WhitelistMap = _WHITELIST_MAP, **json_kwargs: object
) -> str:
    """Serialize an object to a JSON string.

    Objects are first converted to a JSON-serializable form with `pack_value`.
    """
    packed_value = pack_value(val, whitelist_map=whitelist_map)
    return seven.json.dumps(packed_value, **json_kwargs)


@overload
def pack_value(
    val: T_Scalar, whitelist_map: WhitelistMap = ..., descent_path: Optional[str] = ...
) -> T_Scalar:
    ...


@overload
def pack_value(
    val: Union[
        Mapping[str, PackableValue], Set[PackableValue], FrozenSet[PackableValue], NamedTuple, Enum
    ],
    whitelist_map: WhitelistMap = ...,
    descent_path: Optional[str] = ...,
) -> Mapping[str, JsonSerializableValue]:
    ...


@overload
def pack_value(
    val: Sequence[PackableValue],
    whitelist_map: WhitelistMap = ...,
    descent_path: Optional[str] = ...,
) -> Sequence[JsonSerializableValue]:
    ...


def pack_value(
    val: PackableValue,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    descent_path: Optional[str] = None,
) -> JsonSerializableValue:
    """Convert an object into a json serializable complex of dicts, lists, and scalars.

    The following types are transformed in to dicts with special marker keys:
        * whitelisted named tuples
        * whitelisted enums
        * set
        * frozenset
    """
    descent_path = _root(val) if descent_path is None else descent_path
    return _pack_value(val, whitelist_map=whitelist_map, descent_path=_root(val))


def _pack_value(
    val: PackableValue, whitelist_map: WhitelistMap, descent_path: str
) -> JsonSerializableValue:
    if is_named_tuple_instance(val):
        klass_name = val.__class__.__name__
        if not whitelist_map.has_tuple_entry(klass_name):
            raise SerializationError(
                (
                    "Can only serialize whitelisted namedtuples, received"
                    f" {val}.{_path_msg(descent_path)}"
                ),
            )
        serializer = whitelist_map.get_tuple_entry(klass_name)
        return serializer.pack(val, whitelist_map, descent_path)
    if isinstance(val, Enum):
        klass_name = val.__class__.__name__
        if not whitelist_map.has_enum_entry(klass_name):
            raise SerializationError(
                (
                    "Can only serialize whitelisted Enums, received"
                    f" {klass_name}.{_path_msg(descent_path)}"
                ),
            )
        enum_serializer = whitelist_map.get_enum_entry(klass_name)
        return {"__enum__": enum_serializer.pack(val, whitelist_map, descent_path)}
    if isinstance(val, (int, float, str, bool)) or val is None:
        return val
    if isinstance(val, collections.abc.Sequence):
        return [
            _pack_value(item, whitelist_map, f"{descent_path}[{idx}]")
            for idx, item in enumerate(val)
        ]
    if isinstance(val, set):
        set_path = descent_path + "{}"
        return {
            "__set__": [
                _pack_value(item, whitelist_map, set_path) for item in sorted(list(val), key=str)
            ]
        }
    if isinstance(val, frozenset):
        frz_set_path = descent_path + "{}"
        return {
            "__frozenset__": [
                _pack_value(item, whitelist_map, frz_set_path)
                for item in sorted(list(val), key=str)
            ]
        }
    if isinstance(val, collections.abc.Mapping):
        return {
            key: _pack_value(value, whitelist_map, f"{descent_path}.{key}")
            for key, value in val.items()
        }

    # list/dict checks above don't fully cover Sequence/Mapping
    return val


###################################################################################################
# Deserialize / Unpack
###################################################################################################

T_PackableValue = TypeVar("T_PackableValue", bound=PackableValue, default=PackableValue)
U_PackableValue = TypeVar("U_PackableValue", bound=PackableValue, default=PackableValue)


@overload
def deserialize_value(
    val: str,
    as_type: Tuple[Type[T_PackableValue], Type[U_PackableValue]],
    whitelist_map: WhitelistMap = ...,
) -> Union[T_PackableValue, U_PackableValue]:
    ...


@overload
def deserialize_value(
    val: str,
    as_type: Type[T_PackableValue],
    whitelist_map: WhitelistMap = ...,
) -> T_PackableValue:
    ...


@overload
def deserialize_value(
    val: str,
    as_type: None = ...,
    whitelist_map: WhitelistMap = ...,
) -> PackableValue:
    ...


def deserialize_value(
    val: str,
    as_type: Optional[
        Union[Type[T_PackableValue], Tuple[Type[T_PackableValue], Type[U_PackableValue]]]
    ] = None,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> Union[PackableValue, T_PackableValue, Union[T_PackableValue, U_PackableValue]]:
    """Deserialize a json encoded string to a Python object.

    Three steps:

    - Parse the input string as JSON.
    - Unpack the complex of lists, dicts, and scalars resulting from JSON parsing into a complex of richer
      Python objects (e.g. dagster-specific `NamedTuple` objects).
    - Optionally, check that the resulting object is of the expected type.
    """
    check.str_param(val, "val")

    # `metadata_entries` as a constructor argument is deprecated, but it is still used by serdes
    # machinery.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        packed_value = seven.json.loads(val)
        unpacked_value = unpack_value(packed_value, whitelist_map=whitelist_map)
        if as_type and not (
            is_named_tuple_instance(unpacked_value)
            if as_type is NamedTuple
            else isinstance(unpacked_value, as_type)
        ):
            raise DeserializationError(
                f"Deserialized object was not expected type {as_type}, got {type(unpacked_value)}"
            )
        return unpacked_value


@overload
def unpack_value(
    val: JsonSerializableValue,
    as_type: Tuple[Type[T_PackableValue], Type[U_PackableValue]],
    whitelist_map: WhitelistMap = ...,
    descent_path: str = ...,
) -> Union[T_PackableValue, U_PackableValue]:
    ...


@overload
def unpack_value(
    val: JsonSerializableValue,
    as_type: Type[T_PackableValue],
    whitelist_map: WhitelistMap = ...,
    descent_path: str = ...,
) -> T_PackableValue:
    ...


@overload
def unpack_value(
    val: JsonSerializableValue,
    as_type: None = ...,
    whitelist_map: WhitelistMap = ...,
    descent_path: str = ...,
) -> PackableValue:
    ...


def unpack_value(
    val: JsonSerializableValue,
    as_type: Optional[
        Union[Type[T_PackableValue], Tuple[Type[T_PackableValue], Type[U_PackableValue]]]
    ] = None,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    descent_path: Optional[str] = None,
) -> Union[PackableValue, T_PackableValue, Union[T_PackableValue, U_PackableValue]]:
    """Convert a JSON-serializable complex of dicts, lists, and scalars into domain objects.

    Dicts with special keys are processed specially:
    - {"__set__": [...]}: becomes a set()
    - {"__frozenset__": [...]}: becomes a frozenset()
    - {"__enum__": "<class>.<name>"}: becomes an Enum class[name], where `class` is an Enum descendant
    - {"__class__": "<class>", ...}: becomes a NamedTuple, where `class` is a NamedTuple descendant
    """
    descent_path = _root(val) if descent_path is None else descent_path
    unpacked_value = _unpack_value(
        val,
        whitelist_map,
        descent_path,
    )
    if as_type and not (
        is_named_tuple_instance(unpacked_value)
        if as_type is NamedTuple
        else isinstance(unpacked_value, as_type)
    ):
        raise DeserializationError(
            f"Unpacked object was not expected type {as_type}, got {type(val)}"
        )
    return unpacked_value


def _unpack_value(
    val: JsonSerializableValue, whitelist_map: WhitelistMap, descent_path: str
) -> PackableValue:
    if isinstance(val, list):
        return [
            _unpack_value(item, whitelist_map, f"{descent_path}[{idx}]")
            for idx, item in enumerate(val)
        ]
    if isinstance(val, dict) and val.get("__class__"):
        klass_name = cast(str, val.pop("__class__"))
        if not whitelist_map.has_tuple_entry(klass_name):
            raise DeserializationError(
                f'Attempted to deserialize class "{klass_name}" which is not in the whitelist. '
                "This error can occur due to version skew, verify processes are running "
                f"expected versions.{_path_msg(descent_path)}"
            )

        serializer = whitelist_map.get_tuple_entry(klass_name)
        return serializer.unpack(val, whitelist_map, descent_path)
    if isinstance(val, dict) and val.get("__enum__"):
        enum = cast(str, val["__enum__"])
        name, member = enum.split(".")
        if not whitelist_map.has_enum_entry(name):
            raise DeserializationError(
                f"Attempted to deserialize enum {name} which was not in the whitelist.\n"
                "This error can occur due to version skew, verify processes are running "
                f"expected versions.{_path_msg(descent_path)}"
            )
        enum_serializer = whitelist_map.get_enum_entry(name)
        return enum_serializer.unpack(member)
    if isinstance(val, dict) and "__set__" in val:
        set_path = descent_path + "{}"
        items = cast(List[JsonSerializableValue], val["__set__"])
        return set([_unpack_value(item, whitelist_map, set_path) for item in items])
    if isinstance(val, dict) and "__frozenset__" in val:
        frz_set_path = descent_path + "{}"
        items = cast(List[JsonSerializableValue], val["__frozenset__"])
        return frozenset([_unpack_value(item, whitelist_map, frz_set_path) for item in items])
    if isinstance(val, dict):
        return {
            key: _unpack_value(value, whitelist_map, f"{descent_path}.{key}")
            for key, value in val.items()
        }

    return val


###################################################################################################
# Validation
###################################################################################################


def _check_serdes_tuple_class_invariants(klass: Type[NamedTuple]) -> None:
    sig_params = signature(klass.__new__).parameters
    dunder_new_params = list(sig_params.values())

    cls_param = dunder_new_params[0]

    def _with_header(msg: str) -> str:
        return f"For namedtuple {klass.__name__}: {msg}"

    if cls_param.name not in {"cls", "_cls"}:
        raise SerdesUsageError(
            _with_header(f'First parameter must be _cls or cls. Got "{cls_param.name}".')
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

            raise SerdesUsageError(_with_header(error_msg))

        value_param = value_params[index]
        if value_param.name != field:
            error_msg = (
                "Params to __new__ must match the order of field declaration in the namedtuple. "
                'Declared field number {one_based_index} in the namedtuple is "{field_name}". '
                'Parameter {one_based_index} in __new__ method is "{param_name}".'
            ).format(one_based_index=index + 1, field_name=field, param_name=value_param.name)
            raise SerdesUsageError(_with_header(error_msg))

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
                raise SerdesUsageError(_with_header(error_msg))


###################################################################################################
# Utilities
###################################################################################################


def _path_msg(descent_path: str) -> str:
    if not descent_path:
        return ""
    else:
        return f"\nDescent path: {descent_path}"


def _root(val: Any) -> str:
    return f"<root:{val.__class__.__name__}>"


# The below utilities are intended for use in `after_pack` and `before_unpack` hooks in custom
# namedtuple serializers. They help in manipulating the packed representation of various objects.


def is_packed_enum(val: object) -> TypeGuard[Mapping[str, str]]:
    return isinstance(val, dict) and "__enum__" in val


def copy_packed_set(
    packed_set: Mapping[str, Sequence[JsonSerializableValue]],
    as_type: Literal["__frozenset__", "__set__"],
) -> Mapping[str, Sequence[JsonSerializableValue]]:
    """Returns a copy of the packed collection."""
    if "__set__" in packed_set:
        return {as_type: packed_set["__set__"]}
    elif "__frozenset__" in packed_set:
        return {as_type: packed_set["__frozenset__"]}
    else:
        check.failed(f"Invalid packed set: {packed_set}")
