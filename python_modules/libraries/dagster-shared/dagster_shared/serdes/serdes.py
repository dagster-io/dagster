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
import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import is_dataclass
from enum import Enum
from functools import cached_property, partial
from inspect import Parameter, signature
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Final,
    Generic,
    NamedTuple,
    Optional,
    Union,
    cast,
    overload,
)

from pydantic import BaseModel
from typing_extensions import Self, TypeAlias, TypeGuard, TypeVar

import dagster_shared.check as check
from dagster_shared import seven
from dagster_shared.dagster_model.pydantic_compat_layer import model_fields
from dagster_shared.record import (
    IHaveNew,
    as_dict_for_new,
    get_record_annotations,
    has_generated_new,
    is_record,
)
from dagster_shared.serdes.errors import DeserializationError, SerdesUsageError, SerializationError
from dagster_shared.utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    # There is no actual class backing Dataclasses, _typeshed provides this
    # protocol.
    from _typeshed import DataclassInstance


# copied from dagster._utils
def is_named_tuple_instance(obj: object) -> TypeGuard[NamedTuple]:
    return isinstance(obj, tuple) and hasattr(obj, "_fields")


# copied from dagster._utils
def is_named_tuple_subclass(klass: type[object]) -> TypeGuard[type[NamedTuple]]:
    return isinstance(klass, type) and issubclass(klass, tuple) and hasattr(klass, "_fields")


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
    BaseModel,
    "DataclassInstance",
    set["PackableValue"],
    frozenset["PackableValue"],
    Enum,
    IHaveNew,  # indirect way of indicating @record_custom classes are packable
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
    BaseModel,
    "DataclassInstance",
    set["PackableValue"],
    frozenset["PackableValue"],
    Enum,
    "UnknownSerdesValue",
    IHaveNew,
]

SerializableObject: TypeAlias = Union[
    NamedTuple,
    BaseModel,
    "DataclassInstance",
]

_K = TypeVar("_K")
_V = TypeVar("_V")


class SerializableNonScalarKeyMapping(Mapping[_K, _V]):
    """Wrapper class for non-scalar key mappings, used to performantly type check when serializing
    without impacting the performance of serializing the more common scalar key dicts.
    May be replaceable with a different clever scheme.
    """

    def __init__(self, mapping: Mapping[_K, _V] = {}) -> None:
        self.mapping: Mapping[_K, _V] = mapping

    def __setitem__(self, key: _K, item: _V):
        raise NotImplementedError("SerializableNonScalarKeyMapping is immutable")

    def __getitem__(self, item: _K) -> _V:
        return self.mapping[item]

    def __len__(self) -> int:
        return len(self.mapping)

    def __iter__(self) -> Iterator[_K]:
        return iter(self.mapping)


###################################################################################################
# Whitelisting
###################################################################################################


class WhitelistMap(NamedTuple):
    object_serializers: dict[str, "ObjectSerializer"]
    object_deserializers: dict[str, "ObjectSerializer"]
    enum_serializers: dict[str, "EnumSerializer"]
    object_type_map: dict[str, type]

    def register_object(
        self,
        name: str,
        object_class: type,
        serializer_class: type["ObjectSerializer"],
        storage_name: Optional[str] = None,
        old_storage_names: Optional[AbstractSet[str]] = None,
        storage_field_names: Optional[Mapping[str, str]] = None,
        old_fields: Optional[Mapping[str, JsonSerializableValue]] = None,
        skip_when_empty_fields: Optional[AbstractSet[str]] = None,
        skip_when_none_fields: Optional[AbstractSet[str]] = None,
        field_serializers: Optional[Mapping[str, type["FieldSerializer"]]] = None,
        kwargs_fields: Optional[AbstractSet[str]] = None,
    ):
        """Register a model class in the whitelist map.

        Args:
            name: The class name of the namedtuple to register
            object_class: The object class to register.
                Can be None to gracefull load previously serialized objects as None.
            serializer: The class to use when serializing and deserializing
        """
        serializer = serializer_class(
            klass=object_class,
            storage_name=storage_name,
            storage_field_names=storage_field_names,
            old_fields=old_fields,
            skip_when_empty_fields=skip_when_empty_fields,
            skip_when_none_fields=skip_when_none_fields,
            field_serializers=(
                {k: klass.get_instance() for k, klass in field_serializers.items()}
                if field_serializers
                else None
            ),
            kwargs_fields=kwargs_fields,
        )
        self.object_serializers[name] = serializer
        deserializer_name = storage_name or name
        if deserializer_name in self.object_deserializers:
            raise SerdesUsageError(
                f"Multiple deserializers registered for storage name `{deserializer_name}`"
            )
        self.object_deserializers[deserializer_name] = serializer
        if old_storage_names:
            for old_storage_name in old_storage_names:
                self.object_deserializers[old_storage_name] = serializer

        self.object_type_map[name] = serializer.klass

    def register_enum(
        self,
        name: str,
        enum_class: type[Enum],
        serializer_class: Optional[type["EnumSerializer"]] = None,
        storage_name: Optional[str] = None,
        old_storage_names: Optional[AbstractSet[str]] = None,
    ) -> None:
        serializer_class = serializer_class or EnumSerializer
        serializer = serializer_class(
            klass=enum_class,
            storage_name=storage_name,
        )
        self.enum_serializers[name] = serializer
        if storage_name:
            self.enum_serializers[storage_name] = serializer
        if old_storage_names:
            for old_storage_name in old_storage_names:
                self.enum_serializers[old_storage_name] = serializer

    @staticmethod
    def create() -> "WhitelistMap":
        return WhitelistMap(
            object_serializers={},
            object_deserializers={},
            enum_serializers={},
            object_type_map={},
        )


_WHITELIST_MAP: Final[WhitelistMap] = WhitelistMap.create()

T = TypeVar("T")
U = TypeVar("U")
T_Type = TypeVar("T_Type", bound=type[object])
T_Scalar = TypeVar("T_Scalar", bound=Union[str, int, float, bool, None])


@overload
def whitelist_for_serdes(__cls: T_Type) -> T_Type: ...


@overload
def whitelist_for_serdes(
    __cls: None = None,
    *,
    serializer: Optional[type["Serializer"]] = ...,
    storage_name: Optional[str] = ...,
    old_storage_names: Optional[AbstractSet[str]] = None,
    storage_field_names: Optional[Mapping[str, str]] = ...,
    old_fields: Optional[Mapping[str, JsonSerializableValue]] = ...,
    skip_when_empty_fields: Optional[AbstractSet[str]] = ...,
    skip_when_none_fields: Optional[AbstractSet[str]] = ...,
    field_serializers: Optional[Mapping[str, type["FieldSerializer"]]] = None,
    kwargs_fields: Optional[AbstractSet[str]] = None,
) -> Callable[[T_Type], T_Type]: ...


def whitelist_for_serdes(
    __cls: Optional[T_Type] = None,
    *,
    serializer: Optional[type["Serializer"]] = None,
    storage_name: Optional[str] = None,
    old_storage_names: Optional[AbstractSet[str]] = None,
    storage_field_names: Optional[Mapping[str, str]] = None,
    old_fields: Optional[Mapping[str, JsonSerializableValue]] = None,
    skip_when_empty_fields: Optional[AbstractSet[str]] = None,
    skip_when_none_fields: Optional[AbstractSet[str]] = None,
    field_serializers: Optional[Mapping[str, type["FieldSerializer"]]] = None,
    kwargs_fields: Optional[AbstractSet[str]] = None,
) -> Union[T_Type, Callable[[T_Type], T_Type]]:
    """Decorator to whitelist an object (NamedTuple / dataclass / pydantic model) or
    Enum subclass to be serializable. Various arguments can be passed to alter
    serialization behavior for backcompat purposes.

    Args:
      serializer (Type[Serializer]):
          A custom serializer class to use. Object serializers should inherit from the appropriate
          `ObjectSerializer` subclass and use any of hooks `before_unpack`,
          `after_pack`, and `handle_unpack_error`. For Enums, should inherit from `EnumSerializer`
          and use any of hooks `pack` or `unpack`.
      storage_name (Optional[str]):
          A string that will replace the class name when serializing and deserializing. For example,
          if `StorageFoo` is set as the `storage_name` for `Foo`, then `Foo` will be serialized with
          `"__class__": "StorageFoo"`, and dicts encountered with `"__class__": "StorageFoo"` during
          deserialization will be handled by the `Foo` serializer.
      old_storage_names (Optional[AbstractSet[str]]):
          A set of strings that act as aliases for the target class when deserializing. For example,
          if `OldFoo` is passed as an old storage name for `Foo`, then dicts encountered with
          `"__class__": "OldFoo"` during deserialization will be handled by the `Foo` serializer.
      storage_field_names (Optional[Mapping[str, str]]):
          A mapping of field names to the names used during serializing and deserializing. For
          example, if `{"bar": "baz"}` is passed as `storage_field_names` for `Foo`, then
          serializing `Foo(bar=1)` will give `{"__class__": "Foo", "baz": 1}`, and deserializing
          this dict will give `Foo(bar=1)`. Does not apply to enums.
      old_fields (Optional[Mapping[str, JsonSerializableValue]]):
         A mapping of old field names to default values that will be assigned on serialization. This
         is useful for providing backwards compatibility for fields that have been deleted. For
         example, if `{"bar": None}` is passed as `old_fields` for Foo (which has no defined `bar`
         field), then serializing `Foo(...)` will give `{"__class__": "Foo", "bar": None, ...}`.
         Does not apply to enums.
      skip_when_empty_fields (Optional[AbstractSet[str]]):
          A set of fields that should be skipped when serializing if they are an empty collection
          (list, dict, tuple, or set) or None. This allows a stable snapshot ID to be maintained when a new
          field is added. For example, if `{"bar"}` is passed as `skip_when_empty_fields` for `Foo`,
          then serializing `Foo(bar=[])` will give `{"__class__": "Foo"}` (no `bar` in the
          serialization). This is because the `[]` is an empty list and so is dropped. Does not
          apply to enums.
      skip_when_none_fields (Optional[AbstractSet[str]]):
          A set of fields that should be skipped when serializing if they are None. Unlike `skip_when_empty_fields`,
          this will not skip fields that are empty collections, allowing preservation of a
          distinction between None and empty collections across serialization boundaries. This
          allows a stable snapshot ID to be maintained when a new field is added. For example, if
          `{"bar"}` is passed as `skip_when_none_fields` for `Foo`, then serializing `Foo(bar=None)`
          will give `{"__class__": "Foo"}` (no `bar` in the serialization). This is because the `None`
          is an empty list and so is dropped. Does not apply to enums.
      field_serializers (Optional[Mapping[str, FieldSerializer]]):
          A mapping of field names to `FieldSerializer` classes containing custom serialization
          logic. If a field has an associated `FieldSerializer`, then the `pack` and `unpack`
          methods on the `FieldSerializer` will be used instead of defaults. This is mostly useful
          for data structures that are broadly used throughout the codebase but change format.
          The canonical example is `MetadataFieldSerializer`.  Note that if the field needs to be
          stored under a different name, then it still needs an entry in `storage_field_names` even
          if a `FieldSerializer` is provided. Does not apply to enums.
        kwargs_fields (Optional[AbstractSet[str]]): A set of fields that will be passed to the constructor in kwargs.
    """
    if storage_field_names or old_fields or skip_when_empty_fields or skip_when_none_fields:
        check.invariant(
            serializer is None or issubclass(serializer, ObjectSerializer),
            "storage_field_names, old_fields, skip_when_empty_fields, skip_when_none_fields can only be used with a"
            " ObjectSerializer",
        )
    if __cls is not None:  # decorator invoked directly on class
        check.class_param(__cls, "__cls")
        return _whitelist_for_serdes(
            whitelist_map=_WHITELIST_MAP,
        )(__cls)
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
            skip_when_none_fields=skip_when_none_fields,
            field_serializers=field_serializers,
            kwargs_fields=kwargs_fields,
        )


def _whitelist_for_serdes(
    whitelist_map: WhitelistMap,
    serializer: Optional[type["Serializer"]] = None,
    storage_name: Optional[str] = None,
    old_storage_names: Optional[AbstractSet[str]] = None,
    storage_field_names: Optional[Mapping[str, str]] = None,
    old_fields: Optional[Mapping[str, JsonSerializableValue]] = None,
    skip_when_empty_fields: Optional[AbstractSet[str]] = None,
    skip_when_none_fields: Optional[AbstractSet[str]] = None,
    field_serializers: Optional[Mapping[str, type["FieldSerializer"]]] = None,
    kwargs_fields: Optional[AbstractSet[str]] = None,
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
            _check_serdes_tuple_class_invariants(
                klass,
                kwargs_fields=kwargs_fields,
            )

            whitelist_map.register_object(
                klass.__name__,
                klass,
                serializer or NamedTupleSerializer,
                storage_name=storage_name,
                old_storage_names=old_storage_names,
                storage_field_names=storage_field_names,
                old_fields=old_fields,
                skip_when_empty_fields=skip_when_empty_fields,
                skip_when_none_fields=skip_when_none_fields,
                field_serializers=field_serializers,
                kwargs_fields=kwargs_fields,
            )
            return klass  # type: ignore  # (NamedTuple quirk)

        elif is_dataclass(klass) and (
            serializer is None or issubclass(serializer, DataclassSerializer)
        ):
            whitelist_map.register_object(
                klass.__name__,
                klass,
                serializer or DataclassSerializer,
                storage_name=storage_name,
                old_storage_names=old_storage_names,
                storage_field_names=storage_field_names,
                old_fields=old_fields,
                skip_when_empty_fields=skip_when_empty_fields,
                skip_when_none_fields=skip_when_none_fields,
                field_serializers=field_serializers,
            )
            return klass  # type: ignore
        elif issubclass(klass, BaseModel) and (
            serializer is None or issubclass(serializer, PydanticModelSerializer)
        ):
            whitelist_map.register_object(
                klass.__name__,
                klass,
                serializer or PydanticModelSerializer,
                storage_name=storage_name,
                old_storage_names=old_storage_names,
                storage_field_names=storage_field_names,
                old_fields=old_fields,
                skip_when_empty_fields=skip_when_empty_fields,
                skip_when_none_fields=skip_when_none_fields,
                field_serializers=field_serializers,
            )
            return klass
        else:
            raise SerdesUsageError(f"Can not whitelist class {klass} for serializer {serializer}")

    return __whitelist_for_serdes


def is_whitelisted_for_serdes_object(
    val: Any, whitelist_map: WhitelistMap = _WHITELIST_MAP
) -> bool:
    """Check if object has been decorated with `@whitelist_for_serdes`."""
    if (
        (isinstance(val, tuple) and hasattr(val, "_fields"))  # NamedTuple
        or (is_dataclass(val) and not isinstance(val, type))  # dataclass instance
        or isinstance(val, BaseModel)
    ):
        klass_name = val.__class__.__name__
        return klass_name in whitelist_map.object_serializers

    return False


###################################################################################################
# Serializers
###################################################################################################


class UnpackContext:
    """values are unpacked bottom up."""

    def __init__(self):
        self.observed_unknown_serdes_values: set[UnknownSerdesValue] = set()

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
            self.clear_ignored_unknown_values(obj.value)
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
    def __init__(self, *, klass: type[T_Enum], storage_name: Optional[str] = None):
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


EMPTY_VALUES_TO_SKIP: tuple[None, list[Any], dict[Any, Any], set[Any]] = (
    None,
    [],
    {},
    set(),
)


class ObjectSerializer(Serializer, Generic[T]):
    # NOTE: See `whitelist_for_serdes` docstring for explanations of parameters.
    def __init__(
        self,
        *,
        klass: type[T],
        storage_name: Optional[str] = None,
        storage_field_names: Optional[Mapping[str, str]] = None,
        old_fields: Optional[Mapping[str, JsonSerializableValue]] = None,
        skip_when_empty_fields: Optional[AbstractSet[str]] = None,
        skip_when_none_fields: Optional[AbstractSet[str]] = None,
        field_serializers: Optional[Mapping[str, "FieldSerializer"]] = None,
        kwargs_fields: Optional[AbstractSet[str]] = None,
    ):
        self.klass = klass
        self.storage_name = storage_name
        self.storage_field_names = storage_field_names or {}
        self.loaded_field_names = {v: k for k, v in self.storage_field_names.items()}
        self.old_fields = old_fields or {}
        self.skip_when_empty_fields = skip_when_empty_fields or set()
        self.skip_when_none_fields = skip_when_none_fields or set()
        self.field_serializers = field_serializers or {}
        self.kwargs_fields = kwargs_fields

    @abstractmethod
    def object_as_mapping(self, value: T) -> Mapping[str, PackableValue]: ...

    def unpack(
        self,
        unpacked_dict: dict[str, UnpackedValue],
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> T:
        try:
            unpacked_dict = self.before_unpack(context, unpacked_dict)
            unpacked: dict[str, PackableValue] = {}
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
                        unpacked[loaded_name] = value  # type: ignore # 2 hot 4 cast()

                else:
                    context.clear_ignored_unknown_values(value)

            return self.klass(**unpacked)
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
        unpacked_dict: dict[str, UnpackedValue],
    ) -> dict[str, UnpackedValue]:
        return unpacked_dict

    # Hook: Handle an error that occurs when unpacking an object. Can be used to return a default
    # value.
    def handle_unpack_error(
        self,
        exc: Exception,
        context: UnpackContext,
        storage_dict: dict[str, Any],
    ) -> Any:
        raise exc

    def pack_items(
        self,
        value: T,
        whitelist_map: WhitelistMap,
        object_handler: Callable[[SerializableObject, WhitelistMap, str], JsonSerializableValue],
        descent_path: str,
    ) -> Iterator[tuple[str, JsonSerializableValue]]:
        yield "__class__", self.get_storage_name()
        for key, inner_value in self.object_as_mapping(self.before_pack(value)).items():
            if (key in self.skip_when_empty_fields and inner_value in EMPTY_VALUES_TO_SKIP) or (
                key in self.skip_when_none_fields and inner_value is None
            ):
                continue
            storage_key = self.storage_field_names.get(key, key)
            custom = self.field_serializers.get(key)
            if custom:
                yield (
                    storage_key,
                    custom.pack(
                        inner_value,
                        whitelist_map=whitelist_map,
                        descent_path=f"{descent_path}.{key}",
                    ),
                )
            else:
                yield (
                    storage_key,
                    _transform_for_serialization(
                        inner_value,
                        whitelist_map=whitelist_map,
                        object_handler=object_handler,
                        descent_path=f"{descent_path}.{key}",
                    ),
                )
        for key, default in self.old_fields.items():
            yield key, default

    # Hook: Modify the contents of the object before packing
    def before_pack(self, value: T) -> T:
        return value

    @property
    @abstractmethod
    def constructor_param_names(self) -> Sequence[str]: ...

    def get_storage_name(self) -> str:
        return self.storage_name or self.klass.__name__


T_NamedTuple = TypeVar("T_NamedTuple", default=NamedTuple)


# T_NamedTuple previously had a `NamedTuple` bound, but the bound triggers type errors when a `@record`
# decorated class is bound to the variable. @record actually generates a NamedTuple variant of the
# class that was passed in, but we haven't found out how to communicate that to the type system.
# Instead the type signature of the `@record` decorator passes the input class through unmodified.
# Therefore, we forgo `bound` here so that `NamedTupleSerializer` can be used with `@record`
# classes.
class NamedTupleSerializer(ObjectSerializer[T_NamedTuple]):
    def object_as_mapping(self, value: T_NamedTuple) -> Mapping[str, Any]:
        if is_record(value):
            return as_dict_for_new(value)

        # Value is always a NamedTuple, we just can't express that in the type of T_NamedTuple.
        return value._asdict()  # type: ignore

    @cached_property
    def constructor_param_names(self) -> Sequence[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        if has_generated_new(self.klass):
            return list(get_record_annotations(self.klass).keys())

        names = []
        for name, parameter in signature(self.klass.__new__).parameters.items():
            if parameter.kind is Parameter.VAR_POSITIONAL:
                check.failed("Can not use positional args capture on serdes object.")
            elif parameter.kind is Parameter.VAR_KEYWORD:
                names.extend(
                    check.not_none(
                        self.kwargs_fields,
                        "Must specify kwargs_fields when using kwarg capture in __new__.",
                    )
                )
            else:
                names.append(name)

        return names


# Alias for clarity-- see note on `T_NamedTuple` for the relationship between `NamedTuple` and
# `@record`-decorated classes.
RecordSerializer = NamedTupleSerializer

T_Dataclass = TypeVar("T_Dataclass", bound="DataclassInstance", default="DataclassInstance")


class DataclassSerializer(ObjectSerializer[T_Dataclass]):
    def object_as_mapping(self, value: T_Dataclass) -> Mapping[str, Any]:
        return value.__dict__

    @cached_property
    def constructor_param_names(self) -> Sequence[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return list(f.name for f in dataclasses.fields(self.klass))


T_PydanticModel = TypeVar("T_PydanticModel", bound=BaseModel, default=BaseModel)


class PydanticModelSerializer(ObjectSerializer[T_PydanticModel]):
    def object_as_mapping(self, value: T_PydanticModel) -> Mapping[str, Any]:
        value_dict = value.__dict__

        result = {}
        for key, field in self._model_fields.items():
            if field.alias is None and (
                field.serialization_alias is not None or field.validation_alias is not None
            ):
                raise SerializationError(
                    "Can't serialize pydantic models with serialization or validation aliases. Use "
                    "the storage_field_names argument to whitelist_for_serdes instead."
                )
            result_key = field.alias if field.alias else key
            result[result_key] = value_dict[key]

        return result

    @cached_property
    def constructor_param_names(self) -> Sequence[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return [field.alias or key for key, field in self._model_fields.items()]

    @cached_property
    def _model_fields(self) -> Mapping[str, Any]:
        return model_fields(self.klass)


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
    def unpack(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, sequence_value: Optional[Sequence[Any]], **_kwargs
    ) -> Optional[AbstractSet[Any]]:
        return set(sequence_value) if sequence_value is not None else None

    def pack(
        self,
        set_value: Optional[AbstractSet[Any]],
        whitelist_map: WhitelistMap,
        descent_path: str,
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
    serializable_value = _transform_for_serialization(
        val,
        whitelist_map=whitelist_map,
        object_handler=_wrap_object,
        descent_path=_root(val),
    )
    return seven.json.dumps(serializable_value, **json_kwargs)


@overload
def pack_value(
    val: T_Scalar,
    whitelist_map: WhitelistMap = ...,
    descent_path: Optional[str] = ...,
) -> T_Scalar: ...


@overload  # for all the types that serialize to JSON object
def pack_value(
    val: Union[
        Mapping[str, PackableValue],
        set[PackableValue],
        frozenset[PackableValue],
        NamedTuple,
        "DataclassInstance",
        BaseModel,
        Enum,
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


@overload
def pack_value(
    val: PackableValue,
    whitelist_map: WhitelistMap = ...,
    descent_path: Optional[str] = ...,
) -> JsonSerializableValue: ...


def pack_value(
    val: PackableValue,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    descent_path: Optional[str] = None,
) -> JsonSerializableValue:
    """Convert an object into a json serializable complex of dicts, lists, and scalars.

    The following types are transformed in to dicts with special marker keys:
        * whitelisted objects (NamedTuple, dataclass, or pydantic models)
        * whitelisted enums
        * set
        * frozenset
    """
    descent_path = _root(val) if descent_path is None else descent_path
    return _transform_for_serialization(
        val,
        whitelist_map=whitelist_map,
        descent_path=descent_path,
        object_handler=_pack_object,
    )


def _transform_for_serialization(
    val: PackableValue,
    whitelist_map: WhitelistMap,
    object_handler: Callable[[SerializableObject, WhitelistMap, str], JsonSerializableValue],
    descent_path: str,
) -> JsonSerializableValue:
    # this is a hot code path so we handle the common base cases without isinstance
    tval = type(val)
    if tval in (int, float, str, bool) or val is None:
        return val  # type: ignore # 2 hot 4 cast()
    if tval is list:
        return [
            _transform_for_serialization(
                item,
                whitelist_map,
                object_handler,
                f"{descent_path}[{idx}]",
            )
            for idx, item in enumerate(cast(list, val))
        ]
    if tval is dict:
        return {
            key: _transform_for_serialization(
                value,
                whitelist_map,
                object_handler,
                f"{descent_path}.{key}",
            )
            for key, value in cast(dict, val).items()
        }
    if tval is SerializableNonScalarKeyMapping:
        return {
            "__mapping_items__": [
                [
                    _transform_for_serialization(
                        k,
                        whitelist_map,
                        object_handler,
                        f"{descent_path}.{k}",
                    ),
                    _transform_for_serialization(
                        v,
                        whitelist_map,
                        object_handler,
                        f"{descent_path}.{k}",
                    ),
                ]
                for k, v in cast(dict, val).items()
            ]
        }

    if isinstance(val, Enum):
        klass_name = val.__class__.__name__
        if klass_name not in whitelist_map.enum_serializers:
            raise SerializationError(
                "Can only serialize whitelisted Enums, received"
                f" {klass_name}.\nDescent path: {descent_path}",
            )
        enum_serializer = whitelist_map.enum_serializers[klass_name]
        return {"__enum__": enum_serializer.pack(val, whitelist_map, descent_path)}
    if (
        (isinstance(val, tuple) and hasattr(val, "_fields"))
        or isinstance(val, BaseModel)
        or (is_dataclass(val) and not isinstance(val, type))
    ):
        klass_name = val.__class__.__name__
        if klass_name not in whitelist_map.object_serializers:
            raise SerializationError(
                "Can only serialize whitelisted namedtuples, received"
                f" {val}.\nDescent path: {descent_path}",
            )
        return object_handler(
            cast(SerializableObject, val),
            whitelist_map,
            descent_path,
        )
    if isinstance(val, set):
        set_path = descent_path + "{}"
        return {
            "__set__": [
                _transform_for_serialization(
                    item,
                    whitelist_map,
                    object_handler,
                    set_path,
                )
                for item in sorted(list(val), key=str)
            ]
        }
    if isinstance(val, frozenset):
        frz_set_path = descent_path + "{}"
        return {
            "__frozenset__": [
                _transform_for_serialization(
                    item,
                    whitelist_map,
                    object_handler,
                    frz_set_path,
                )
                for item in sorted(list(val), key=str)
            ]
        }

    # custom string subclasses
    if isinstance(val, str):
        return val

    # handle more expensive and uncommon abc instance checks last
    if isinstance(val, collections.abc.Mapping):
        return {
            key: _transform_for_serialization(
                value,
                whitelist_map,
                object_handler,
                f"{descent_path}.{key}",
            )
            for key, value in val.items()
        }
    if isinstance(val, collections.abc.Sequence):
        return [
            _transform_for_serialization(
                item,
                whitelist_map,
                object_handler,
                f"{descent_path}[{idx}]",
            )
            for idx, item in enumerate(val)
        ]

    raise SerializationError(f"Unhandled value type {tval}")


def _pack_object(
    obj: SerializableObject, whitelist_map: WhitelistMap, descent_path: str
) -> Mapping[str, JsonSerializableValue]:
    # the object_handler for _transform_for_serialization to produce dicts for objects

    klass_name = obj.__class__.__name__
    serializer = whitelist_map.object_serializers[klass_name]
    return dict(serializer.pack_items(obj, whitelist_map, _pack_object, descent_path))


class _LazySerializationWrapper(dict):
    """An object used to allow us to drive serialization iteratively
    over the tree of objects via json.dumps, instead of having to create
    an entire tree of primitive objects to pass to json.dumps.
    """

    __slots__ = [
        "_descent_path",
        "_obj",
        "_whitelist_map",
    ]

    def __init__(
        self,
        obj: SerializableObject,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ):
        self._obj = obj
        self._whitelist_map = whitelist_map
        self._descent_path = descent_path

        # populate backing native dict to work around c fast path check
        # https://github.com/python/cpython/blob/0fb18b02c8ad56299d6a2910be0bab8ad601ef24/Modules/_json.c#L1542
        super().__init__({"__serdes": "wrapper"})

    def items(self) -> Iterator[tuple[str, JsonSerializableValue]]:  # pyright: ignore[reportIncompatibleMethodOverride]
        klass_name = self._obj.__class__.__name__
        serializer = self._whitelist_map.object_serializers[klass_name]
        yield from serializer.pack_items(
            self._obj, self._whitelist_map, _wrap_object, self._descent_path
        )


def _wrap_object(
    obj: SerializableObject,
    whitelist_map: WhitelistMap,
    descent_path: str,
) -> "_LazySerializationWrapper":
    # the object_handler for _transform_for_serialization to use in conjunction with json.dumps for iterative serialization
    return _LazySerializationWrapper(obj, whitelist_map, descent_path)


###################################################################################################
# Deserialize / Unpack
###################################################################################################

T_PackableValue = TypeVar("T_PackableValue", bound=PackableValue, default=PackableValue)
U_PackableValue = TypeVar("U_PackableValue", bound=PackableValue, default=PackableValue)


@overload
def deserialize_value(
    val: str,
    as_type: tuple[type[T_PackableValue], type[U_PackableValue]],
    whitelist_map: WhitelistMap = ...,
) -> Union[T_PackableValue, U_PackableValue]: ...


@overload
def deserialize_value(
    val: str,
    as_type: type[T_PackableValue],
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
        Union[type[T_PackableValue], tuple[type[T_PackableValue], type[U_PackableValue]]]
    ] = None,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> Union[PackableValue, T_PackableValue, Union[T_PackableValue, U_PackableValue]]:
    """Deserialize a json encoded string to a Python object.

    Two steps:

    - Parse the input string as JSON with an object_hook for custom types.
    - Optionally, check that the resulting object is of the expected type.
    """
    check.str_param(val, "val")

    return deserialize_values([val], as_type, whitelist_map)[0]


@overload
def deserialize_values(
    vals: Iterable[str],
    as_type: type[T_PackableValue],
    whitelist_map: WhitelistMap = ...,
) -> Sequence[T_PackableValue]: ...


@overload
def deserialize_values(
    vals: Iterable[str],
    as_type: None = ...,
    whitelist_map: WhitelistMap = ...,
) -> Sequence[PackableValue]: ...


@overload
def deserialize_values(
    vals: Iterable[str],
    as_type: Optional[
        Union[type[T_PackableValue], tuple[type[T_PackableValue], type[U_PackableValue]]]
    ],
    whitelist_map: WhitelistMap = ...,
) -> Sequence[Union[PackableValue, T_PackableValue, Union[T_PackableValue, U_PackableValue]]]: ...


def deserialize_values(
    vals: Iterable[str],
    as_type: Optional[
        Union[type[T_PackableValue], tuple[type[T_PackableValue], type[U_PackableValue]]]
    ] = None,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> Sequence[Union[PackableValue, T_PackableValue, Union[T_PackableValue, U_PackableValue]]]:
    """Deserialize a collection of values without having to repeatedly exit/enter the deserializing context."""
    with (
        disable_dagster_warnings(),
        check.EvalContext.contextual_namespace(whitelist_map.object_type_map),
    ):
        unpacked_values = []
        for val in vals:
            context = UnpackContext()
            unpacked_value = seven.json.loads(
                val,
                object_hook=partial(_unpack_object, whitelist_map=whitelist_map, context=context),
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
            unpacked_values.append(unpacked_value)

    return unpacked_values


class UnknownSerdesValue:
    def __init__(self, message: str, value: Mapping[str, UnpackedValue]):
        self.message = message
        self.value = value


def _unpack_object(val: dict, whitelist_map: WhitelistMap, context: UnpackContext) -> UnpackedValue:
    if "__class__" in val:
        klass_name = val["__class__"]
        if klass_name not in whitelist_map.object_deserializers:
            return context.observe_unknown_value(
                UnknownSerdesValue(
                    f'Attempted to deserialize class "{klass_name}" which is not in the whitelist.',
                    val,
                )
            )

        val.pop("__class__")
        deserializer = whitelist_map.object_deserializers[klass_name]
        return deserializer.unpack(val, whitelist_map, context)

    if "__enum__" in val:
        enum = cast(str, val["__enum__"])
        name, member = enum.split(".")
        if name not in whitelist_map.enum_serializers:
            return context.observe_unknown_value(
                UnknownSerdesValue(
                    f"Attempted to deserialize enum {name} which was not in the whitelist.",
                    val,
                )
            )

        enum_serializer = whitelist_map.enum_serializers[name]
        return enum_serializer.unpack(member)

    if "__set__" in val:
        items = cast(list[JsonSerializableValue], val["__set__"])
        return set(items)

    if "__frozenset__" in val:
        items = cast(list[JsonSerializableValue], val["__frozenset__"])
        return frozenset(items)

    if "__mapping_items__" in val:
        return {
            cast(Any, _unpack_value(k, whitelist_map, context)): _unpack_value(
                v, whitelist_map, context
            )
            for k, v in val["__mapping_items__"]
        }

    return val


@overload
def unpack_value(
    val: JsonSerializableValue,
    as_type: tuple[type[T_PackableValue], type[U_PackableValue]],
    whitelist_map: WhitelistMap = ...,
    context: Optional[UnpackContext] = ...,
) -> Union[T_PackableValue, U_PackableValue]: ...


@overload
def unpack_value(
    val: JsonSerializableValue,
    as_type: type[T_PackableValue],
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
        Union[type[T_PackableValue], tuple[type[T_PackableValue], type[U_PackableValue]]]
    ] = None,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    context: Optional[UnpackContext] = None,
) -> Union[PackableValue, T_PackableValue, Union[T_PackableValue, U_PackableValue]]:
    """Convert a JSON-serializable complex of dicts, lists, and scalars into domain objects.

    Dicts with special keys are processed specially:
    - {"__set__": [...]}: becomes a set()
    - {"__frozenset__": [...]}: becomes a frozenset()
    - {"__enum__": "<class>.<name>"}: becomes an Enum class[name], where `class` is an Enum descendant
    - {"__class__": "<class>", ...}: becomes an instance of the class, where `class` is a
        NamedTuple, dataclass or pydantic model
    """
    context = UnpackContext() if context is None else context
    unpacked_value = _unpack_value(
        val,
        whitelist_map,
        context,
    )
    unpacked_value = context.finalize_unpack(unpacked_value)
    if as_type and not isinstance(unpacked_value, as_type):
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


def _check_serdes_tuple_class_invariants(
    klass: type[NamedTuple],
    kwargs_fields: Optional[AbstractSet[str]],
) -> None:
    # can skip validation on @record generated new
    if has_generated_new(klass):
        return

    sig_params = signature(klass.__new__).parameters
    dunder_new_params = list(sig_params.values())

    cls_param = dunder_new_params[0]

    def _with_header(msg: str) -> str:
        return f"For {klass.__name__}: {msg}"

    if cls_param.name not in {"cls", "_cls"}:
        raise SerdesUsageError(
            _with_header(f'First parameter must be _cls or cls. Got "{cls_param.name}".')
        )

    value_params = dunder_new_params[1:]

    for index, field in enumerate(klass._fields):
        if index >= len(value_params):
            if value_params[-1].kind is Parameter.VAR_KEYWORD:
                if kwargs_fields is None:
                    raise SerdesUsageError(
                        _with_header(
                            "kwargs capture used in __new__ but kwargs_fields was not specified. "
                            "Declare the set of fields processed via kwargs as kwargs_fields "
                            f"Expecting: {list(klass._fields[index:])!r}"
                        )
                    )
                elif field not in kwargs_fields:
                    raise SerdesUsageError(
                        _with_header(
                            f'Expected field "{field}" in kwargs_fields but it was not specified.'
                        )
                    )

            else:
                error_msg = (
                    "Missing parameters to __new__. You have declared fields "
                    "that are not present as parameters to the "
                    "to the __new__ method. In order for "
                    "both serdes serialization and pickling to work, "
                    "these must match or kwargs and kwargs_fields must be used. "
                    f"Missing: {list(klass._fields[index:])!r}"
                )

                raise SerdesUsageError(_with_header(error_msg))

        if not is_record(klass):
            # non @record NamedTuples get pickled via ordinal args, so ensure ordering
            value_param = value_params[index]
            if value_param.name != field:
                error_msg = (
                    "Params to __new__ must match the order of field declaration for "
                    "NamedTuples that are not @record based. "
                    f'Declared field number {index + 1} in the namedtuple is "{field}". '
                    f'Parameter {index + 1} in __new__ method is "{value_param.name}".'
                )
                raise SerdesUsageError(_with_header(error_msg))

    if len(value_params) > len(klass._fields):
        # Ensure that remaining parameters have default values
        for extra_param_index in range(len(klass._fields), len(value_params) - 1):
            if value_params[extra_param_index].default == Parameter.empty:
                error_msg = (
                    f'Parameter "{value_params[extra_param_index].name}" is a parameter to the __new__ '
                    "method but is not a field in this namedtuple. The only "
                    "reason why this should exist is that "
                    "it is a field that used to exist (we refer to this as the graveyard) "
                    "but no longer does. However it might exist in historical storage. This "
                    "parameter existing ensures that serdes continues to work. However these "
                    "must come at the end and have a default value for pickling to work."
                )
                raise SerdesUsageError(_with_header(error_msg))


###################################################################################################
# Utilities
###################################################################################################


def _root(val: Any) -> str:
    return f"<root:{val.__class__.__name__}>"


def get_storage_name(klass: type, *, whitelist_map: WhitelistMap = _WHITELIST_MAP):
    if klass.__name__ not in whitelist_map.object_serializers:
        check.failed(f"{klass.__name__} is not a known serializable object type.")
    ser = whitelist_map.object_serializers[klass.__name__]
    return ser.get_storage_name()


def get_storage_fields(klass: type, whitelist_map: WhitelistMap = _WHITELIST_MAP):
    if klass.__name__ not in whitelist_map.object_serializers:
        check.failed(f"{klass.__name__} is not a known serializable object type.")
    ser = whitelist_map.object_serializers[klass.__name__]
    # get the current fields
    current_fields = ser.constructor_param_names
    # remap defined storage field names
    stored_fields = [ser.storage_field_names.get(f, f) for f in current_fields]
    # insert old fields
    stored_fields.extend(ser.old_fields.keys())
    # we sort_keys=True in json dump
    return sorted(stored_fields)


_OBJECT_START = '{"__class__":'


def get_prefix_for_a_serialized(klass: type, *, whitelist_map=_WHITELIST_MAP):
    """Returns the expected start of the string for a serdes serialized object
    of the passed type.
    """
    return f'{_OBJECT_START} "{get_storage_name(klass, whitelist_map=whitelist_map)}"'
