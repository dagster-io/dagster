import dataclasses
from typing import Any


@dataclasses.dataclass(frozen=True)
class Ref:
    name: str


@dataclasses.dataclass(frozen=True)
class SerdesField:
    name: str
    type_str: str | None


@dataclasses.dataclass(frozen=True)
class SerdesObject:
    typename: str
    class_name: str
    storage_name: str
    class_type: str
    serializer_type: str
    fields: list[SerdesField]
    base_classes: list[str] | None = None
    field_mappings: dict[str, str] | None = None
    old_fields: dict[str, Any] | None = None
    skip_when_empty: list[str] | None = None
    skip_when_none: list[str] | None = None
    is_record: bool | None = None


@dataclasses.dataclass(frozen=True)
class SerdesEnum:
    typename: str
    enum_name: str
    storage_name: str
    class_type: str
    members: list[str]


@dataclasses.dataclass(frozen=True)
class SerdesUnion:
    typename: str
    base_class: str
    implementations: list[str]


@dataclasses.dataclass(frozen=True)
class BuiltinType:
    typename: str
    description: str
