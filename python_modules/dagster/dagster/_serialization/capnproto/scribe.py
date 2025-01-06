import datetime
from asyncio import as_completed, gather
from collections.abc import Collection, Iterable
from enum import Enum
from inspect import _empty, isabstract
from os import PathLike
from typing import (
    AbstractSet,
    Any,
    AsyncGenerator,
    Awaitable,
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
from dagster._serialization.base.scribe import (
    BANISHED_FROM_SERDES,
    BaseScribe,
    ScribeCoatCheck,
    ScribeCoatCheckTicket,
)
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
    UnfinishedCapnProtoFieldType,
)
from dagster._utils import check


# This is a recursive type that I'm not going to spend time figuring out at the moment.
def _is_json_serializable(type_: Any) -> bool:
    return set(get_args(type_)) == set(get_args(JsonSerializableValue))


TRULY_ANYTHING = CapnProtoUnionMetadata([CapnProtoPointerType.ANY_POINTER, *CapnProtoPrimitiveType])


class CapnProtoScribe(BaseScribe[CapnProtoMessageMetadata]):
    async def visit_message(self, serializer: ObjectSerializer[Any]) -> CapnProtoMessageMetadata:
        return CapnProtoMessageMetadata(serializer, [])

    async def visit_field(
        self, message: CapnProtoMessageMetadata, name: str, field_type: Type[Any]
    ):
        serializer = message.serializer
        check.invariant(
            isinstance(serializer, EnumSerializer) or isinstance(serializer, ObjectSerializer),
            "Annoying type checking",
        )
        message_type = serializer.klass  # type: ignore
        inner_type = await self._translate_type(field_type, self._type_key(message_type))
        message.fields.append(CapnProtoFieldMetadata(name, inner_type))

    async def visit_enum(
        self, serializer: EnumSerializer[Enum]
    ) -> CapnProtoMessageMetadata[CapnProtoFieldType]:
        return CapnProtoMessageMetadata(
            serializer,
            [
                CapnProtoFieldMetadata(member.name, CapnProtoPrimitiveType.VOID)
                for member in serializer.klass
            ],
            is_enum=True,
        )

    async def _translate_type(
        self, wrapped_type: Type[Any], message_type_key: str
    ) -> UnfinishedCapnProtoFieldType:
        if isinstance(wrapped_type, type) and self._type_key(wrapped_type) == message_type_key:
            return CapnProtoRecursiveType.SELF

        wrapped_type = normalize_type(wrapped_type)

        if _is_json_serializable(wrapped_type):
            return TRULY_ANYTHING

        unwrapped_type = unwrap_type(wrapped_type)

        # We need un-annotated types for issubclass checks sometimes
        args = get_args(unwrapped_type)
        if get_origin(unwrapped_type) is not None:
            normalized_type = cast(Type, get_origin(unwrapped_type))
        else:
            normalized_type = cast(Type, unwrapped_type)

        if normalized_type is type(None):
            # REVIEW: NoneType could be translated to a VOID in capnproto but not worth it.
            check.failed("NoneType should not be used in serialization")
        elif normalized_type is Any or normalized_type is object:
            # REVIEW: lame af
            return TRULY_ANYTHING
        elif isinstance(normalized_type, ForwardRef):
            # Recursive type
            check.invariant(
                normalized_type.__forward_arg__ == "self",
                "ForwardRef should only be used for recursive types",
            )
            return CapnProtoRecursiveType.SELF
        elif normalized_type is type:
            check.failed("Type type should not be used in serialization")
        elif normalized_type is _empty:
            check.failed("Missing type annotations")
        elif normalized_type is Collection or normalized_type is Iterable:
            check.failed("Too ambiguous")
        elif normalized_type is DagsterEventType or normalized_type is ObjectStoreOperationType:
            # REVIEW: these should be serdes enums, unclear why they are not
            return CapnProtoPrimitiveType.TEXT

        primitive = CapnProtoPrimitiveType.from_type(normalized_type)
        if primitive:
            return primitive
        elif normalized_type is datetime.datetime:
            return CapnProtoPrimitiveType.FLOAT64
        elif normalized_type is PathLike:
            # REVIEW: this is a protocol for AnyStr. There's probably a cleaner way to resolve protocols
            return CapnProtoPrimitiveType.TEXT
        elif normalized_type is Union:
            inner_types = []
            for arg in args:
                inner_type = await self._translate_type(arg, message_type_key)
                if isinstance(inner_type, CapnProtoUnionMetadata):
                    # This shouldn't really happen but collapse the union types
                    inner_types.extend(f for f in inner_type.fields)
                else:
                    inner_types.append(inner_type)
            return CapnProtoUnionMetadata(inner_types)
        elif normalized_type is Literal:
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
            return self._get_expected_scribed_type(enum_type, message_type_key)
        elif issubclass(normalized_type, Tuple):
            return CapnProtoStructMetadata(
                [await self._translate_type(arg, message_type_key) for arg in args]
            )
        elif issubclass(normalized_type, Enum):
            return self._get_expected_scribed_type(normalized_type, message_type_key)
        elif issubclass(normalized_type, FrozenSet):
            # REVIEW: I'm not sure anybody really types stuff FrozenSet, we tend to type using AbstractSet and then
            # use a frozen set.
            return CapnProtoCollectionType(
                CapnProtoPointerType.FROZENSET,
                await self._translate_type(args[0], message_type_key),
            )
        elif issubclass(normalized_type, Set) or issubclass(normalized_type, AbstractSet):
            return CapnProtoCollectionType(
                CapnProtoPointerType.SET, await self._translate_type(args[0], message_type_key)
            )
        elif issubclass(normalized_type, List) or issubclass(normalized_type, Sequence):
            return CapnProtoCollectionType(
                CapnProtoPointerType.LIST,
                await self._translate_type(args[0], message_type_key),
            )
        elif issubclass(normalized_type, Dict) or issubclass(normalized_type, Mapping):
            # REVIEW: I would like to validate that the keys are always strings but that's not possible
            # because of the packing and unpacking of these maps in serdes, which allows keys to be any type
            return CapnProtoCollectionType(
                CapnProtoPointerType.MAP, await self._translate_type(args[1], message_type_key)
            )
        elif isabstract(normalized_type) and normalized_type.__module__.startswith("dagster."):
            # Treat this as a union of all subclasses
            inner_types = []
            for subclass in normalized_type.__subclasses__():
                if not isabstract(subclass) and subclass not in BANISHED_FROM_SERDES:
                    inner_types.append(await self._translate_type(subclass, message_type_key))
            return CapnProtoUnionMetadata(inner_types)
        else:
            return self._get_expected_scribed_type(normalized_type, message_type_key)

    async def finalize(self) -> AsyncGenerator[Tuple[Type[Any], CapnProtoMessageMetadata], None]:
        if any(
            (
                not willcall.future.done()
                or willcall.future.cancelled()
                or willcall.future.exception()
            )
            for willcall in self._scribed_types.values()
        ):
            check.failed("Not all types scribed")

        async def _finalize_tuple(
            type_and_willcall: Tuple[str, ScribeCoatCheck[CapnProtoMessageMetadata]],
        ) -> Tuple[str, CapnProtoMessageMetadata]:
            type_name, willcall = type_and_willcall
            root_message = willcall.future.result()
            return (
                type_name,
                await self._finalize_message(root_message, ScribeCoatCheckTicket(type_name)),
            )

        tasks: Iterable[Awaitable] = [_finalize_tuple(t) for t in self._scribed_types.items()]
        for task in as_completed(tasks, timeout=10):
            yield await task

    async def _finalize_message_field(
        self,
        field: CapnProtoFieldMetadata[UnfinishedCapnProtoFieldType],
        root_message: ScribeCoatCheckTicket,
    ) -> CapnProtoFieldMetadata[CapnProtoFieldType]:
        return CapnProtoFieldMetadata(
            field.name,
            await self._finalize_field_type(field.type_, root_message),
        )

    async def _finalize_message(
        self,
        metadata: CapnProtoMessageMetadata[UnfinishedCapnProtoFieldType],
        root_message: ScribeCoatCheckTicket,
    ) -> CapnProtoMessageMetadata[CapnProtoFieldType]:
        final_fields = await gather(
            *(self._finalize_message_field(field, root_message) for field in metadata.fields)
        )
        return CapnProtoMessageMetadata(metadata.serializer, final_fields, metadata.is_enum)

    async def _finalize_field_type(
        self, field_type: UnfinishedCapnProtoFieldType, root_message: ScribeCoatCheckTicket
    ) -> CapnProtoFieldType:
        if isinstance(field_type, ScribeCoatCheckTicket):
            return await self._scribed_types[field_type.type_].future
        elif isinstance(field_type, CapnProtoUnionMetadata):
            new_fields = await gather(
                *(self._finalize_field_type(f, root_message) for f in field_type.fields)
            )
            return CapnProtoUnionMetadata(new_fields)
        elif isinstance(field_type, CapnProtoStructMetadata):
            new_fields = await gather(
                *(self._finalize_field_type(f, root_message) for f in field_type.fields)
            )
            return CapnProtoStructMetadata(new_fields)
        elif isinstance(field_type, CapnProtoCollectionType):
            new_generic_arg = await self._finalize_field_type(field_type.generic_arg, root_message)
            return CapnProtoCollectionType(field_type.collection_base_type, new_generic_arg)
        elif isinstance(field_type, CapnProtoMessageMetadata):
            return await self._finalize_message(field_type, root_message)
        else:
            return field_type
