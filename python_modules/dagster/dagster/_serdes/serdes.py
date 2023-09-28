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
from abc import ABC, abstractmethod
from enum import Enum
from functools import partial
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
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
    overload,
)

from typing_extensions import Final, Self, TypeAlias, TypeVar

import dagster._check as check
import dagster._seven as seven
from dagster._utils import is_named_tuple_instance, is_named_tuple_subclass
from dagster._utils.cached_method import cached_method
from dagster._utils.warnings import disable_dagster_warnings

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

UnpackedValue: TypeAlias = Union[
    Sequence["UnpackedValue"],
    Mapping[str, "UnpackedValue"],
    str,
    int,
    float,
    bool,
    None,
    NamedTuple,
    Set["PackableValue"],
    FrozenSet["PackableValue"],
    Enum,
    "UnknownSerdesValue",
]


###################################################################################################
# Whitelisting
###################################################################################################


class WhitelistMap(NamedTuple):
    tuple_serializers: Dict[str, "NamedTupleSerializer"]
    tuple_deserializers: Dict[str, "NamedTupleSerializer"]
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
            field_serializers=(
                {k: klass.get_instance() for k, klass in field_serializers.items()}
                if field_serializers
                else None
            ),
        )
        self.tuple_serializers[name] = serializer
        deserializer_name = storage_name or name
        self.tuple_deserializers[deserializer_name] = serializer
        if old_storage_names:
            for old_storage_name in old_storage_names:
                self.tuple_deserializers[old_storage_name] = serializer

    def has_tuple_serializer(self, name: str) -> bool:
        return name in self.tuple_serializers

    def has_tuple_deserializer(self, name: str) -> bool:
        return name in self.tuple_deserializers

    def get_tuple_serializer(self, name: str) -> "NamedTupleSerializer":
        return self.tuple_serializers[name]

    def get_tuple_deserializer(self, name: str) -> "NamedTupleSerializer":
        return self.tuple_deserializers[name]

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
        return WhitelistMap(tuple_serializers={}, tuple_deserializers={}, enums={})


_WHITELIST_MAP: Final[WhitelistMap] = WhitelistMap.create()

T = TypeVar("T")
U = TypeVar("U")
T_Type = TypeVar("T_Type", bound=Type[object])
T_Scalar = TypeVar("T_Scalar", bound=Union[str, int, float, bool, None])


@overload
def whitelist_for_serdes(__cls: T_Type) -> T_Type: ...


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
) -> Callable[[T_Type], T_Type]: ...


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
            "storage_field_names, old_fields, skip_when_empty_fields can only be used with a"
            " NamedTupleSerializer",
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


###################################################################################################
# Serializers
###################################################################################################


class UnpackContext:
    """values are unpacked bottom up."""

    def __init__(self):
        self.observed_unknown_serdes_values: Set[UnknownSerdesValue] = set()

    def assert_no_unknown_values(self, obj: UnpackedValue) -> PackableValue:
        if isinstance(obj, UnknownSerdesValue):
            raise DeserializationError(
                f"{obj.message}\nThis error can occur due to version skew, verify processes are"
                " running expected versions."
            )
        elif isinstance(obj, (list, set, frozenset)):
            for inner in obj:
                self.assert_no_unknown_values(inner)
        elif isinstance(obj, dict):
            for v in obj.values():
                self.assert_no_unknown_values(v)

        return cast(PackableValue, obj)

    def observe_unknown_value(self, val: "UnknownSerdesValue") -> "UnknownSerdesValue":
        self.observed_unknown_serdes_values.add(val)
        return val

    def clear_ignored_unknown_values(self, obj: T) -> T:
        if isinstance(obj, UnknownSerdesValue):
            self.observed_unknown_serdes_values.discard(obj)
        elif isinstance(obj, (list, set, frozenset)):
            for inner in obj:
                self.clear_ignored_unknown_values(inner)
        elif isinstance(obj, dict):
            for v in obj.values():
                self.clear_ignored_unknown_values(v)

        return obj

    def finalize_unpack(self, unpacked: UnpackedValue) -> PackableValue:
        if self.observed_unknown_serdes_values:
            message = ",".join(v.message for v in self.observed_unknown_serdes_values)
            raise DeserializationError(
                f"{message}\nThis error can occur due to version skew, verify processes are"
                " running expected versions."
            )
        return cast(PackableValue, unpacked)


class Serializer(ABC):
    pass


T_Enum = TypeVar("T_Enum", bound=Enum, default=Enum)


class EnumSerializer(Serializer, Generic[T_Enum]):
    def __init__(self, *, klass: Type[T_Enum], storage_name: Optional[str] = None):
        self.klass = klass
        self.storage_name = storage_name

    def unpack(self, value: str) -> T_Enum:
        return self.klass[value]

    def pack(
        self,
        value: Enum,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> str:
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
        self.loaded_field_names = {v: k for k, v in self.storage_field_names.items()}
        self.old_fields = old_fields or {}
        self.skip_when_empty_fields = skip_when_empty_fields or set()
        self.field_serializers = field_serializers or {}

    def unpack(
        self,
        unpacked_dict: Dict[str, UnpackedValue],
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> T_NamedTuple:
        try:
            unpacked_dict = self.before_unpack(context, unpacked_dict)
            unpacked: Dict[str, PackableValue] = {}
            for key, value in unpacked_dict.items():
                loaded_name = self.loaded_field_names.get(key, key)
                # Naively implements backwards compatibility by filtering arguments that aren't present in
                # the constructor. If a property is present in the serialized object, but doesn't exist in
                # the version of the class loaded into memory, that property will be completely ignored.
                if loaded_name in self.constructor_param_names:
                    # custom unpack regardless of hook vs recursive descent
                    custom = self.field_serializers.get(loaded_name)
                    if custom:
                        unpacked[loaded_name] = custom.unpack(
                            value,
                            whitelist_map=whitelist_map,
                            context=context,
                        )
                    elif context.observed_unknown_serdes_values:
                        unpacked[loaded_name] = context.assert_no_unknown_values(value)
                    else:
                        unpacked[loaded_name] = cast(PackableValue, value)

                else:
                    context.clear_ignored_unknown_values(value)

            # False positive type error here due to an eccentricity of `NamedTuple`-- calling `NamedTuple`
            # directly acts as a class factory, which is not true for `NamedTuple` subclasses (which act
            # like normal constructors). Because we have no subclass info here, the type checker thinks
            # we are invoking the class factory and complains about arguments.
            return self.klass(**unpacked)  # type: ignore
        except Exception as exc:
            value = self.handle_unpack_error(exc, context, unpacked_dict)
            if isinstance(context, UnpackContext):
                context.assert_no_unknown_values(value)
                context.clear_ignored_unknown_values(unpacked_dict)
            return value

    # Hook: Modify the contents of the unpacked dict before domain object construction during
    # deserialization.
    def before_unpack(
        self,
        context: UnpackContext,
        unpacked_dict: Dict[str, UnpackedValue],
    ) -> Dict[str, UnpackedValue]:
        return unpacked_dict

    # Hook: Handle an error that occurs when unpacking a NamedTuple. Can be used to return a default
    # value.
    def handle_unpack_error(
        self,
        exc: Exception,
        context: UnpackContext,
        storage_dict: Dict[str, Any],
    ) -> Any:
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
            storage_key = self.storage_field_names.get(key, key)
            custom = self.field_serializers.get(key)
            if custom:
                packed[storage_key] = custom.pack(
                    inner_value,
                    whitelist_map=whitelist_map,
                    descent_path=f"{descent_path}.{key}",
                )
            else:
                packed[storage_key] = _pack_value(
                    inner_value,
                    whitelist_map=whitelist_map,
                    descent_path=f"{descent_path}.{key}",
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
        __unpacked_value: UnpackedValue,
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> PackableValue: ...

    @abstractmethod
    def pack(
        self,
        __unpacked_value: Any,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue: ...


class SetToSequenceFieldSerializer(FieldSerializer):
    def unpack(
        self, sequence_value: Optional[Sequence[Any]], **_kwargs
    ) -> Optional[AbstractSet[Any]]:
        return set(sequence_value) if sequence_value is not None else None

    def pack(
        self, set_value: Optional[AbstractSet[Any]], whitelist_map: WhitelistMap, descent_path: str
    ) -> Optional[Sequence[Any]]:
        return (
            sorted([pack_value(x, whitelist_map, descent_path) for x in set_value], key=str)
            if set_value is not None
            else None
        )


###################################################################################################
# Serialize / Pack
###################################################################################################


def serialize_value(
    val: PackableValue,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    **json_kwargs: Any,
) -> str:
    """Serialize an object to a JSON string.

    Objects are first converted to a JSON-serializable form with `pack_value`.
    """
    packed_value = pack_value(val, whitelist_map=whitelist_map)
    return seven.json.dumps(packed_value, **json_kwargs)


@overload
def pack_value(
    val: T_Scalar,
    whitelist_map: WhitelistMap = ...,
    descent_path: Optional[str] = ...,
) -> T_Scalar: ...


@overload
def pack_value(
    val: Union[
        Mapping[str, PackableValue], Set[PackableValue], FrozenSet[PackableValue], NamedTuple, Enum
    ],
    whitelist_map: WhitelistMap = ...,
    descent_path: Optional[str] = ...,
) -> Mapping[str, JsonSerializableValue]: ...


@overload
def pack_value(
    val: Sequence[PackableValue],
    whitelist_map: WhitelistMap = ...,
    descent_path: Optional[str] = ...,
) -> Sequence[JsonSerializableValue]: ...


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
    return _pack_value(val, whitelist_map=whitelist_map, descent_path=descent_path)


def _pack_value(
    val: PackableValue,
    whitelist_map: WhitelistMap,
    descent_path: str,
) -> JsonSerializableValue:
    # this is a hot code path so we handle the common base cases without isinstance
    tval = type(val)
    if tval in (int, float, str, bool) or val is None:
        return cast(JsonSerializableValue, val)
    if tval is list:
        return [
            _pack_value(item, whitelist_map, f"{descent_path}[{idx}]")
            for idx, item in enumerate(cast(list, val))
        ]
    if tval is dict:
        return {
            key: _pack_value(value, whitelist_map, f"{descent_path}.{key}")
            for key, value in cast(dict, val).items()
        }

    # inlined is_named_tuple_instance
    if isinstance(val, tuple) and hasattr(val, "_fields"):
        klass_name = val.__class__.__name__
        if not whitelist_map.has_tuple_serializer(klass_name):
            raise SerializationError(
                "Can only serialize whitelisted namedtuples, received"
                f" {val}.\nDescent path: {descent_path}",
            )
        serializer = whitelist_map.get_tuple_serializer(klass_name)
        return serializer.pack(cast(NamedTuple, val), whitelist_map, descent_path)
    if isinstance(val, Enum):
        klass_name = val.__class__.__name__
        if not whitelist_map.has_enum_entry(klass_name):
            raise SerializationError(
                "Can only serialize whitelisted Enums, received"
                f" {klass_name}.\nDescent path: {descent_path}",
            )
        enum_serializer = whitelist_map.get_enum_entry(klass_name)
        return {"__enum__": enum_serializer.pack(val, whitelist_map, descent_path)}
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

    # custom string subclasses
    if isinstance(val, str):
        return val

    # handle more expensive and uncommon abc instance checks last
    if isinstance(val, collections.abc.Mapping):
        return {
            key: _pack_value(value, whitelist_map, f"{descent_path}.{key}")
            for key, value in val.items()
        }
    if isinstance(val, collections.abc.Sequence):
        return [
            _pack_value(item, whitelist_map, f"{descent_path}[{idx}]")
            for idx, item in enumerate(val)
        ]

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
) -> Union[T_PackableValue, U_PackableValue]: ...


@overload
def deserialize_value(
    val: str,
    as_type: Type[T_PackableValue],
    whitelist_map: WhitelistMap = ...,
) -> T_PackableValue: ...


@overload
def deserialize_value(
    val: str,
    as_type: None = ...,
    whitelist_map: WhitelistMap = ...,
) -> PackableValue: ...


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

    # Never issue warnings when deserializing deprecated objects.
    with disable_dagster_warnings():
        context = UnpackContext()
        unpacked_value = seven.json.loads(
            val, object_hook=partial(_unpack_object, whitelist_map=whitelist_map, context=context)
        )
        unpacked_value = context.finalize_unpack(unpacked_value)
        if as_type and not (
            is_named_tuple_instance(unpacked_value)
            if as_type is NamedTuple
            else isinstance(unpacked_value, as_type)
        ):
            raise DeserializationError(
                f"Deserialized object was not expected type {as_type}, got {type(unpacked_value)}"
            )

    return unpacked_value


class UnknownSerdesValue:
    def __init__(self, message: str, value: Mapping[str, UnpackedValue]):
        self.message = message
        self.value = value


def _unpack_object(val: dict, whitelist_map: WhitelistMap, context: UnpackContext):
    if "__class__" in val:
        klass_name = cast(str, val["__class__"])
        if not whitelist_map.has_tuple_deserializer(klass_name):
            return context.observe_unknown_value(
                UnknownSerdesValue(
                    f'Attempted to deserialize class "{klass_name}" which is not in the whitelist.',
                    val,
                )
            )

        val.pop("__class__")
        deserializer = whitelist_map.get_tuple_deserializer(klass_name)
        return deserializer.unpack(val, whitelist_map, context)

    if "__enum__" in val:
        enum = cast(str, val["__enum__"])
        name, member = enum.split(".")
        if not whitelist_map.has_enum_entry(name):
            return context.observe_unknown_value(
                UnknownSerdesValue(
                    f"Attempted to deserialize enum {name} which was not in the whitelist.",
                    val,
                )
            )

        enum_serializer = whitelist_map.get_enum_entry(name)
        return enum_serializer.unpack(member)

    if "__set__" in val:
        items = cast(List[JsonSerializableValue], val["__set__"])
        return set(items)

    if "__frozenset__" in val:
        items = cast(List[JsonSerializableValue], val["__frozenset__"])
        return frozenset(items)

    return val


@overload
def unpack_value(
    val: JsonSerializableValue,
    as_type: Tuple[Type[T_PackableValue], Type[U_PackableValue]],
    whitelist_map: WhitelistMap = ...,
    context: Optional[UnpackContext] = ...,
) -> Union[T_PackableValue, U_PackableValue]: ...


@overload
def unpack_value(
    val: JsonSerializableValue,
    as_type: Type[T_PackableValue],
    whitelist_map: WhitelistMap = ...,
    context: Optional[UnpackContext] = ...,
) -> T_PackableValue: ...


@overload
def unpack_value(
    val: JsonSerializableValue,
    as_type: None = ...,
    whitelist_map: WhitelistMap = ...,
    context: Optional[UnpackContext] = ...,
) -> PackableValue: ...


def unpack_value(
    val: JsonSerializableValue,
    as_type: Optional[
        Union[Type[T_PackableValue], Tuple[Type[T_PackableValue], Type[U_PackableValue]]]
    ] = None,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    context: Optional[UnpackContext] = None,
) -> Union[PackableValue, T_PackableValue, Union[T_PackableValue, U_PackableValue]]:
    """Convert a JSON-serializable complex of dicts, lists, and scalars into domain objects.

    Dicts with special keys are processed specially:
    - {"__set__": [...]}: becomes a set()
    - {"__frozenset__": [...]}: becomes a frozenset()
    - {"__enum__": "<class>.<name>"}: becomes an Enum class[name], where `class` is an Enum descendant
    - {"__class__": "<class>", ...}: becomes a NamedTuple, where `class` is a NamedTuple descendant
    """
    context = UnpackContext() if context is None else context
    unpacked_value = _unpack_value(
        val,
        whitelist_map,
        context,
    )
    unpacked_value = context.finalize_unpack(unpacked_value)
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
    val: JsonSerializableValue,
    whitelist_map: WhitelistMap,
    context: UnpackContext,
) -> UnpackedValue:
    if isinstance(val, list):
        return [_unpack_value(item, whitelist_map, context) for item in val]

    if isinstance(val, dict):
        unpacked_vals = {k: _unpack_value(v, whitelist_map, context) for k, v in val.items()}
        return _unpack_object(unpacked_vals, whitelist_map, context)

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
                f"these must match. Missing: {list(klass._fields[index:])!r}"
            )

            raise SerdesUsageError(_with_header(error_msg))

        value_param = value_params[index]
        if value_param.name != field:
            error_msg = (
                "Params to __new__ must match the order of field declaration in the namedtuple. "
                f'Declared field number {index + 1} in the namedtuple is "{field}". '
                f'Parameter {index + 1} in __new__ method is "{value_param.name}".'
            )
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


def _root(val: Any) -> str:
    return f"<root:{val.__class__.__name__}>"
