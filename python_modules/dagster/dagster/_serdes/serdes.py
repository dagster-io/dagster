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

import collections.abc
import warnings
from abc import ABC, abstractmethod
from enum import Enum
from inspect import Parameter, signature
from typing import (
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

from typing_extensions import Final, TypeAlias, TypeVar

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


class TupleEntry(NamedTuple):
    # if None, object is deserialized as None
    named_tuple_class: Optional[Type[NamedTuple]]
    serializer: Type["NamedTupleSerializer"]
    args_for_class: Mapping[str, Parameter]
    storage_class_name: Optional[str]
    storage_field_names: Mapping[str, str]

    def get_storage_class_name(self) -> str:
        return self.storage_class_name or self.named_tuple_class.__name__  # type: ignore  # (possible none)

    @cached_method
    def get_storage_field_name(self, field: str) -> str:
        return self.storage_field_names.get(field, field)

    @cached_method
    def get_loaded_field_name(self, field: str) -> str:
        for k, v in self.storage_field_names.items():
            if v == field:
                return k
        return field


EnumEntry: TypeAlias = Tuple[Type[Enum], Type["EnumSerializer"]]


class WhitelistMap(NamedTuple):
    tuples: Dict[str, TupleEntry]
    enums: Dict[str, EnumEntry]
    nulls: Set[str]

    def register_tuple(
        self,
        name: str,
        named_tuple_class: Optional[Type[NamedTuple]],
        serializer: Optional[Type["NamedTupleSerializer"]],
        storage_class_name: Optional[str] = None,
        storage_field_names: Optional[Mapping[str, str]] = None,
    ):
        """Register a tuple in the whitelist map.

        Args:
            name: The class name of the namedtuple to register
            nt: The namedtuple class to register.
                Can be None to gracefull load previously serialized objects as None.
            serializer: The class to use when serializing and deserializing
        """
        args_for_class = signature(named_tuple_class.__new__).parameters
        entry = TupleEntry(
            named_tuple_class,
            serializer or DefaultNamedTupleSerializer,
            args_for_class,
            storage_class_name,
            storage_field_names or {},
        )
        self.tuples[name] = entry
        if storage_class_name:
            self.tuples[storage_class_name] = entry

    def has_tuple_entry(self, name: str) -> bool:
        return name in self.tuples

    def get_tuple_entry(self, name: str) -> TupleEntry:
        return self.tuples[name]

    def register_enum(
        self,
        name: str,
        enum_class: Type[Enum],
        serializer: Optional[Type["EnumSerializer"]],
    ) -> None:
        self.enums[name] = (enum_class, serializer or DefaultEnumSerializer)

    def has_enum_entry(self, name: str) -> bool:
        return name in self.enums

    def get_enum_entry(self, name: str) -> EnumEntry:
        return self.enums[name]

    def register_null(self, name: str) -> None:
        self.nulls.add(name)

    def has_null_entry(self, name: str) -> bool:
        return name in self.nulls

    @staticmethod
    def create() -> "WhitelistMap":
        return WhitelistMap(tuples={}, enums={}, nulls=set())


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
    storage_field_names: Optional[Mapping[str, str]] = ...,
) -> Callable[[T_Type], T_Type]:
    ...


def whitelist_for_serdes(
    __cls: Optional[T_Type] = None,
    *,
    serializer: Optional[Type["Serializer"]] = None,
    storage_name: Optional[str] = None,
    storage_field_names: Optional[Mapping[str, str]] = None,
) -> Union[T_Type, Callable[[T_Type], T_Type]]:
    """
    Decorator to whitelist a NamedTuple or enum to be serializable. If a `storage_name` is provided
    for a NamedTuple, then serialized instances of the NamedTuple will be stored under the
    `storage_name` instead of the class name. This is primarily useful for maintaining backwards
    compatibility. If a serialized object undergoes a name change, then setting `storage_name` to
    the old name will (a) allow the object to be deserialized by versions of Dagster prior to the
    name change; (b) allow Dagster to load objects stored using the old name.

    @whitelist_for_serdes
    class

    """
    if storage_name or storage_field_names:
        check.invariant(
            serializer is None or issubclass(serializer, DefaultNamedTupleSerializer),
            "storage_name storage_field_names can only be used with DefaultNamedTupleSerializer",
        )
    if __cls is not None:  # decorator invoked directly on class
        check.class_param(__cls, "__cls")
        return _whitelist_for_serdes(whitelist_map=_WHITELIST_MAP)(__cls)
    else:  # decorator passed params
        check.opt_class_param(serializer, "serializer", superclass=Serializer)
        return _whitelist_for_serdes(
            whitelist_map=_WHITELIST_MAP, serializer=serializer, storage_name=storage_name
        )


def _whitelist_for_serdes(
    whitelist_map: WhitelistMap,
    serializer: Optional[Type["Serializer"]] = None,
    storage_name: Optional[str] = None,
    storage_field_names: Optional[Mapping[str, str]] = None,
) -> Callable[[T_Type], T_Type]:
    def __whitelist_for_serdes(klass: T_Type) -> T_Type:
        if issubclass(klass, Enum) and (
            serializer is None or issubclass(serializer, EnumSerializer)
        ):
            whitelist_map.register_enum(klass.__name__, klass, serializer)
            return klass
        elif is_named_tuple_subclass(klass) and (
            serializer is None or issubclass(serializer, NamedTupleSerializer)
        ):
            _check_serdes_tuple_class_invariants(klass)
            whitelist_map.register_tuple(
                klass.__name__, klass, serializer, storage_name, storage_field_names
            )
            return klass  # type: ignore  # (NamedTuple quirk)
        else:
            raise SerdesUsageError(f"Can not whitelist class {klass} for serializer {serializer}")

    return __whitelist_for_serdes


class Serializer(ABC):
    pass


class EnumSerializer(Serializer):
    @classmethod
    @abstractmethod
    def value_from_storage_str(cls, storage_str: str, klass: Type[Any]) -> Enum:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def value_to_storage_str(
        cls, value: Enum, whitelist_map: WhitelistMap, descent_path: str
    ) -> str:
        raise NotImplementedError()


class DefaultEnumSerializer(EnumSerializer):
    @classmethod
    def value_from_storage_str(cls, storage_str: str, klass: Type[Any]) -> Enum:
        return getattr(klass, storage_str)

    @classmethod
    def value_to_storage_str(
        cls, value: Enum, whitelist_map: WhitelistMap, descent_path: str
    ) -> str:
        return str(value)


T_NamedTuple = TypeVar("T_NamedTuple", bound=NamedTuple, default=NamedTuple)


class NamedTupleSerializer(Serializer, Generic[T_NamedTuple]):
    @classmethod
    @abstractmethod
    def value_from_storage_dict(
        cls,
        storage_dict: Dict[str, Any],
        klass: Type[T_NamedTuple],
        args_for_class: Mapping[str, Parameter],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> T_NamedTuple:
        """
        Load the target value from the object tree output of json parsing.

        Args:
            storage_dict: The parsed json object to hydrate
            klass: The namedtuple class object
            args_for_class: the inspect.signature paramaters for __new__
            whitelist_map: current map of whitelisted serdes objects
            descent_path: the path to the current node from the root
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def value_to_storage_dict(
        cls,
        value: T_NamedTuple,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Dict[str, JsonSerializableValue]:
        """
        Transform the object in to a form that can be json serialized.

        Args:
            value: the instance of the object
            whitelist_map: current map of whitelisted serdes objects
            descent_path: the path to the current node from the root
        """
        raise NotImplementedError()


EMPTY_VALUES_TO_SKIP: Tuple[None, List[Any], Dict[Any, Any], Set[Any]] = (None, [], {}, set())


class DefaultNamedTupleSerializer(NamedTupleSerializer[T_NamedTuple]):
    @classmethod
    def skip_when_empty(cls) -> Set[str]:
        # Override this method to leave out certain fields from the serialized namedtuple
        # when they are empty. This can be used to ensure that adding a new field doesn't
        # change the serialized namedtuple.
        return set()

    @classmethod
    def value_from_storage_dict(
        cls,
        storage_dict: Dict[str, Any],
        klass: Type[T_NamedTuple],
        args_for_class: Mapping[str, Parameter],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> T_NamedTuple:
        entry = whitelist_map.get_tuple_entry(klass.__name__)

        # Naively implements backwards compatibility by filtering arguments that aren't present in
        # the constructor. If a property is present in the serialized object, but doesn't exist in
        # the version of the class loaded into memory, that property will be completely ignored.
        unpacked_dict = {}
        for key, value in storage_dict.items():
            loaded_name = entry.get_loaded_field_name(field=key)
            if loaded_name in args_for_class:
                unpacked_dict[loaded_name] = unpack_value(
                    value, whitelist_map=whitelist_map, descent_path=f"{descent_path}.{key}"
                )
        return cls.value_from_unpacked(unpacked_dict, klass)

    @classmethod
    def value_from_unpacked(
        cls,
        unpacked_dict: Mapping[str, Any],
        klass: Type[T_NamedTuple],
    ) -> T_NamedTuple:
        # False positive type error here due to an eccentricity of `NamedTuple`-- calling `NamedTuple`
        # directly acts as a class factory, which is not true for `NamedTuple` subclasses (which act
        # like normal constructors). Because we have no subclass info here, the type checker thinks
        # we are invoking the class factory and complains about arguments.
        return cast(T_NamedTuple, klass(**unpacked_dict))  # type: ignore

    @classmethod
    def value_to_storage_dict(
        cls,
        value: T_NamedTuple,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Dict[str, JsonSerializableValue]:
        skip_when_empty_fields = cls.skip_when_empty()

        klass_name = value.__class__.__name__
        entry = whitelist_map.get_tuple_entry(klass_name)

        base_dict: Dict[str, JsonSerializableValue] = {}
        base_dict["__class__"] = entry.get_storage_class_name()
        for key, inner_value in value._asdict().items():
            if key in skip_when_empty_fields and inner_value in EMPTY_VALUES_TO_SKIP:
                continue
            storage_key = entry.get_storage_field_name(field=key)
            base_dict[storage_key] = pack_value(inner_value, whitelist_map, f"{descent_path}.{key}")

        return base_dict


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
    """
    Convert an object into a json serializable complex of dicts, lists, and scalars.

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
        serializer = whitelist_map.get_tuple_entry(klass_name).serializer
        return serializer.value_to_storage_dict(val, whitelist_map, descent_path)
    if isinstance(val, Enum):
        klass_name = val.__class__.__name__
        if not whitelist_map.has_enum_entry(klass_name):
            raise SerializationError(
                (
                    "Can only serialize whitelisted Enums, received"
                    f" {klass_name}.{_path_msg(descent_path)}"
                ),
            )
        _, enum_serializer = whitelist_map.get_enum_entry(klass_name)
        return {"__enum__": enum_serializer.value_to_storage_str(val, whitelist_map, descent_path)}
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
        if whitelist_map.has_null_entry(klass_name):
            return None
        elif not whitelist_map.has_tuple_entry(klass_name):
            raise DeserializationError(
                f"Attempted to deserialize class {klass_name} which is not in the whitelist. "
                "This error can occur due to version skew, verify processes are running "
                f"expected versions.{_path_msg(descent_path)}"
            )

        entry = whitelist_map.get_tuple_entry(klass_name)

        return entry.serializer.value_from_storage_dict(
            val, entry.named_tuple_class, entry.args_for_class, whitelist_map, descent_path  # type: ignore  # (possible none)
        )
    if isinstance(val, dict) and val.get("__enum__"):
        enum = cast(str, val["__enum__"])
        name, member = enum.split(".")
        if not whitelist_map.has_enum_entry(name):
            raise DeserializationError(
                f"Attempted to deserialize enum {name} which was not in the whitelist.\n"
                "This error can occur due to version skew, verify processes are running "
                f"expected versions.{_path_msg(descent_path)}"
            )
        enum_class, enum_serializer = whitelist_map.get_enum_entry(name)
        return enum_serializer.value_from_storage_str(member, enum_class)
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
# Back compat
###################################################################################################


def register_serdes_null_fallbacks(
    fallbacks: Sequence[str],
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> None:
    """
    Manually provide remappings for serialized records.
    Used to load types that no longer exist as None.
    """
    for class_name in fallbacks:
        whitelist_map.register_null(class_name)


def register_serdes_tuple_fallbacks(
    fallback_map: Mapping[str, Optional[Type[NamedTuple]]],
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> None:
    """
    Manually provide remappings for named tuples.
    Used to manage loading previously types that no longer exist.
    """
    for class_name, klass in fallback_map.items():
        serializer = cast(
            Type[NamedTupleSerializer],
            whitelist_map.get_tuple_entry(klass.__name__)[1]
            if klass and whitelist_map.has_tuple_entry(klass.__name__)
            else DefaultNamedTupleSerializer,
        )
        whitelist_map.register_tuple(
            class_name,
            klass,
            serializer,
        )


def register_serdes_enum_fallbacks(
    fallback_map: Mapping[str, Type[Enum]],
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> None:
    """
    Manually provide remappings for named tuples.
    Used to manage loading previously types that no longer exist.
    """
    serializer: Type[EnumSerializer] = DefaultEnumSerializer
    for class_name, klass in fallback_map.items():
        if not klass or not issubclass(klass, Enum):
            raise SerdesUsageError(
                f"Cannot register {klass} as an enum, because it does not have enum type."
            )
        if klass and whitelist_map.has_enum_entry(klass.__name__):
            _, serializer = whitelist_map.get_enum_entry(klass.__name__)
        whitelist_map.register_enum(class_name, klass, serializer)


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


def _path_msg(descent_path: str) -> str:
    if not descent_path:
        return ""
    else:
        return f"\nDescent path: {descent_path}"


def _root(val: Any) -> str:
    return f"<root:{val.__class__.__name__}>"


def replace_storage_keys(
    storage_dict: Dict[str, Any], key_mapping: Mapping[str, str]
) -> Dict[str, Any]:
    """Returns a version of the storage dict that replaces all the keys."""
    result: Dict[str, Any] = {}
    for key, value in storage_dict.items():
        if key not in key_mapping:
            result[key] = value
        else:
            result[key_mapping[key]] = value
    return result
