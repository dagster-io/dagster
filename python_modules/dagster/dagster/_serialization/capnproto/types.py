from enum import Enum, EnumMeta
from typing import Any, List, NamedTuple, Optional, Type, Union

from dagster._serdes.serdes import Serializer

# type alias for all possible types of a field
CapnProtoFieldType = Union[
    "CapnProtoPrimitiveType",
    "CapnProtoPointerType",
    "CapnProtoMessageMetadata",
    "CapnProtoUnionMetadata",
    "CapnProtoStructMetadata",
    "CapnProtoCollectionType",
]


class CapnProtoCollectionType(NamedTuple):
    collection_base_type: str
    generic_arg: CapnProtoFieldType


class CapnProtoFieldMetadata(NamedTuple):
    name: str
    type_: CapnProtoFieldType


class CapnProtoUnionMetadata(NamedTuple):
    fields: List[CapnProtoFieldType]


class CapnProtoStructMetadata(NamedTuple):
    fields: List[CapnProtoFieldType]


# Messages are root-level (in the schema tree) objects
class CapnProtoMessageMetadata(NamedTuple):
    serializer: Serializer
    fields: List[CapnProtoFieldMetadata]
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
