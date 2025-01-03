import datetime
from collections import UserString
from collections.abc import Collection, Iterable
from enum import Enum
from inspect import _empty, isabstract
from os import PathLike
from typing import (
    AbstractSet,
    Any,
    Dict,
    ForwardRef,
    FrozenSet,
    List,
    Literal,
    Mapping,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
    get_args,
    get_origin,
)

from dagster._core.definitions.events import ObjectStoreOperationType
from dagster._core.events import DagsterEventType
from dagster._serdes.serdes import EnumSerializer, JsonSerializableValue, ObjectSerializer
from dagster._serialization.base.scribe import BANISHED_FROM_SERDES, BaseScribe
from dagster._serialization.base.types import normalize_type, unwrap_type
from dagster._serialization.capnproto.types import (
    CapnProtoCollectionType,
    CapnProtoFieldMetadata,
    CapnProtoFieldType,
    CapnProtoMessageMetadata,
    CapnProtoPointerType,
    CapnProtoPrimitiveType,
    CapnProtoRecursiveType,
    CapnProtoStructMetadata,
    CapnProtoUnionMetadata,
)
from dagster._utils import check


# This is a recursive type that I'm not going to spend time figuring out at the moment.
def _is_json_serializable(type_: Any) -> bool:
    return set(get_args(type_)) == set(get_args(JsonSerializableValue))


TRULY_ANYTHING = CapnProtoUnionMetadata([CapnProtoPointerType.ANY_POINTER, *CapnProtoPrimitiveType])


class CapnProtoScribe(BaseScribe[CapnProtoMessageMetadata]):
    async def visit_message(self, serializer: ObjectSerializer[Any]) -> CapnProtoMessageMetadata:
        return CapnProtoMessageMetadata(serializer, [])

    async def visit_field(self, message: CapnProtoMessageMetadata, name: str, type_: Type[Any]):
        if isinstance(message.serializer, EnumSerializer) or isinstance(message.serializer, ObjectSerializer):
            type_name = str(message.serializer.klass) + "." + name
        inner_type = await self._translate_type(type_name, type_)
        message.fields.append(CapnProtoFieldMetadata(name, inner_type))

    async def visit_enum(self, serializer: EnumSerializer[Enum]) -> CapnProtoMessageMetadata:
        return CapnProtoMessageMetadata(
            serializer,
            [
                CapnProtoFieldMetadata(member.name, CapnProtoPrimitiveType.VOID)
                for member in serializer.klass
            ],
            is_enum=True,
        )

    async def _translate_type(
        self, ctx: str, wrapped_type: Type[Any], _recursion_guard: Set[Type[Any]] = set()
    ) -> CapnProtoFieldType:
        wrapped_type = normalize_type(wrapped_type)

        if _is_json_serializable(wrapped_type):
            return TRULY_ANYTHING

        unwrapped_type = unwrap_type(wrapped_type)

        # We need un-annotated types for issubclass checks sometimes
        args = get_args(unwrapped_type)
        if get_origin(unwrapped_type) is not None:
            type_ = cast(Type, get_origin(unwrapped_type))
        else:
            type_ = cast(Type, unwrapped_type)

        if type_ is type(None):
            # REVIEW: NoneType could be translated to a VOID in capnproto but not worth it.
            check.failed("NoneType should not be used in serialization")
        elif type_ is Any or type_ is object:
            # REVIEW: lame af
            return TRULY_ANYTHING
        elif isinstance(type_, ForwardRef):
            # Recursive type
            check.invariant(
                type_.__forward_arg__ == "self",
                "ForwardRef should only be used for recursive types",
            )
            return CapnProtoRecursiveType.SELF
        elif type_ is type:
            check.failed("Type type should not be used in serialization")
        elif type_ is _empty:
            check.failed("Missing type annotations")
        elif type_ is Collection or type_ is Iterable:
            check.failed("Too ambiguous")
        elif type_ is DagsterEventType or type_ is ObjectStoreOperationType:
            # REVIEW: these should be serdes enums, unclear why they are not
            return CapnProtoPrimitiveType.TEXT
        elif type_ is UserString:
            check.failed(f"How did this happen? {wrapped_type} {unwrapped_type} {type_}")
            # REVIEW: no idea how Optional[Sequence[str]] turns into this type at runtime
            return CapnProtoPrimitiveType.TEXT

        primitive = CapnProtoPrimitiveType.from_type(type_)
        if primitive:
            return primitive
        elif type_ is datetime.datetime:
            return CapnProtoPrimitiveType.FLOAT64
        elif type_ is PathLike:
            # REVIEW: this is a protocol for AnyStr. There's probably a cleaner way to resolve protocols
            return CapnProtoPrimitiveType.TEXT
        elif type_ is Union:
            inner_types = []
            for arg in args:
                inner_type = await self._translate_type(ctx, arg, _recursion_guard)
                if isinstance(inner_type, CapnProtoUnionMetadata):
                    # This shouldn't really happen but collapse the union types
                    inner_types.extend(f for f in inner_type.fields)
                else:
                    inner_types.append(inner_type)
            return CapnProtoUnionMetadata(inner_types)
        elif type_ is Literal:
            # A literal should only be used for enums, we just need to figure out what enum it is
            literal_types = {
                (arg.__class__ if isinstance(arg, Enum) else type(arg)) for arg in args
            }
            if len(literal_types) != 1:
                check.failed(f"Literal type {wrapped_type} has multiple types {literal_types}")
            enum_type = next(iter(literal_types))
            if enum_type is DagsterEventType or enum_type is ObjectStoreOperationType:
                # REVIEW: these should be serdes enums, unclear why they are not
                return CapnProtoPrimitiveType.TEXT
            return self._get_expected_scribed_type(enum_type, ctx)
        elif issubclass(type_, Tuple):
            return CapnProtoStructMetadata(
                [await self._translate_type(ctx, arg, _recursion_guard) for arg in args]
            )
        elif issubclass(type_, Enum):
            return self._get_expected_scribed_type(type_, ctx)
        elif issubclass(type_, FrozenSet):
            # REVIEW: I'm not sure anybody really types stuff FrozenSet, we tend to type using AbstractSet and then
            # use a frozen set.
            return CapnProtoCollectionType(
                CapnProtoPointerType.FROZENSET,
                await self._translate_type(ctx, args[0], _recursion_guard),
            )
        elif issubclass(type_, Set) or issubclass(type_, AbstractSet):
            return CapnProtoCollectionType(
                CapnProtoPointerType.SET, await self._translate_type(ctx, args[0], _recursion_guard)
            )
        elif issubclass(type_, List) or issubclass(type_, Sequence):
            return CapnProtoCollectionType(
                CapnProtoPointerType.LIST,
                await self._translate_type(ctx, args[0], _recursion_guard),
            )
        elif issubclass(type_, Dict) or issubclass(type_, Mapping):
            # REVIEW: I would like to validate that the keys are always strings but that's not possible
            # because of the packing and unpacking of these maps in serdes, which allows keys to be any type
            return CapnProtoCollectionType(
                CapnProtoPointerType.MAP, await self._translate_type(ctx, args[1], _recursion_guard)
            )
        elif isabstract(type_) and type_.__module__.startswith("dagster."):
            # Treat this as a union of all subclasses
            inner_types = []
            for subclass in type_.__subclasses__():
                if not isabstract(subclass) and subclass not in BANISHED_FROM_SERDES:
                    inner_types.append(await self._translate_type(ctx, subclass))
            return CapnProtoUnionMetadata(inner_types)
        else:
            return self._get_expected_scribed_type(type_, ctx)
