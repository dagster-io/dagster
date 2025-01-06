from enum import Enum, EnumMeta
from typing import Any, Generic, List, NamedTuple, Optional, Type, TypeVar, Union

from dagster._serdes.serdes import Serializer
from dagster._serialization.base.scribe import ScribeCoatCheckTicket

# type alias for all possible types of a field
UnfinishedCapnProtoFieldType = Union[
    "CapnProtoPrimitiveType",
    "CapnProtoPointerType",
    "CapnProtoMessageMetadata",
    "CapnProtoUnionMetadata",
    "CapnProtoStructMetadata",
    "CapnProtoCollectionType",
    "CapnProtoRecursiveType",
    ScribeCoatCheckTicket,
]

CapnProtoFieldType = Union[
    "CapnProtoPrimitiveType",
    "CapnProtoPointerType",
    "CapnProtoMessageMetadata",
    "CapnProtoUnionMetadata",
    "CapnProtoStructMetadata",
    "CapnProtoCollectionType",
    "CapnProtoRecursiveType",
]

TFieldType = TypeVar("TFieldType")


class CapnProtoCollectionType(Generic[TFieldType], NamedTuple):
    collection_base_type: str
    generic_arg: TFieldType


class CapnProtoFieldMetadata(Generic[TFieldType], NamedTuple):
    name: str
    type_: TFieldType


class CapnProtoUnionMetadata(Generic[TFieldType], NamedTuple):
    fields: List[TFieldType]


class CapnProtoStructMetadata(Generic[TFieldType], NamedTuple):
    fields: List[TFieldType]


# Messages are root-level (in the schema tree) objects
class CapnProtoMessageMetadata(Generic[TFieldType], NamedTuple):
    serializer: Serializer
    fields: List[CapnProtoFieldMetadata[TFieldType]]
    # HACK: just a hack to fit enums into the design, not great but could be easily broken out into another class
    is_enum: bool = False


class CapnProtoPrimitiveTypeMeta(EnumMeta):
    def __contains__(self, item):
        return item in self.__members__


class CapnProtoPrimitiveType(str, Enum, metaclass=CapnProtoPrimitiveTypeMeta):
    VOID = "Void"
    TEXT = "Text"
    INT64 = "Int64"
    FLOAT64 = "Float64"
    BOOL = "Bool"

    @staticmethod
    def from_type(type_: Type[Any]) -> Optional["CapnProtoPrimitiveType"]:
        if type_ is str:
            return CapnProtoPrimitiveType.TEXT
        elif type_ is int:
            return CapnProtoPrimitiveType.INT64
        elif type_ is float:
            return CapnProtoPrimitiveType.FLOAT64
        elif type_ is bool:
            return CapnProtoPrimitiveType.BOOL
        return None

    def __str__(self):
        return self.value


# These are "provided" types either by capnproto (List, Anypointer) or by Dagster (Map, Set, FrozenSet)
class CapnProtoPointerType(str, Enum):
    ANY_POINTER = "AnyPointer"
    LIST = "List"

    MAP = "Map"
    SET = "Set"
    FROZENSET = "FrozenSet"

    def __str__(self):
        return self.value


# Just a sentinel value for recursive types
class CapnProtoRecursiveType(str, Enum):
    SELF = "Self"

    def __str__(self):
        return self.value
