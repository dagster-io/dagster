from enum import Enum
from typing import Any, AsyncGenerator, Generator, List, NamedTuple, Optional, Union, cast

from dagster._serdes.serdes import EnumSerializer, ObjectSerializer
from dagster._serialization.capnproto.types import (
    CapnProtoFieldMetadata,
    CapnProtoFieldType,
    CapnProtoMessageMetadata,
    CapnProtoStructMetadata,
    CapnProtoUnionMetadata,
)


class CapnProtoEnumRenderer(NamedTuple):
    name: str
    members: dict[str, int]

    def render(self, indent: str = "  ") -> Generator[str, None, None]:
        yield f"enum {self.name} {{"
        for member, value in self.members.items():
            yield f"  @{value} {member},"
        yield "}"


class CapnProtoFieldRenderer(NamedTuple):
    name: str
    idx: int
    type_: str

    def render(self, indent: str = "  ") -> Generator[str, None, None]:
        yield f"  @{self.idx} {self.name}: {self.type_};"


class CapnProtoUnionRenderer(NamedTuple):
    name: Optional[str]
    fields: List[CapnProtoFieldRenderer]

    def render(self, indent: str = "  ") -> Generator[str, None, None]:
        name = self.name or ""
        yield f"union {name} {{"
        for field in self.fields:
            yield from field.render(indent)
        yield "}"


class CapnProtoStructRenderer(NamedTuple):
    name: str
    fields: List[Union[CapnProtoFieldRenderer, CapnProtoUnionRenderer]]

    def render(self, indent: str = "  ") -> Generator[str, None, None]:
        yield f"struct {self.name} {{"
        for field in self.fields:
            yield from field.render(indent)
        yield "}"


class CapnProtoFieldIndexer:
    """This class would eventually be able to bridge the indexings of the fields between schema versions."""

    def __init__(self):
        self.idx = 0

    def get_idx(self) -> int:
        # TODO: should look up existing idx in the capnproto schema
        idx = self.idx
        self.idx += 1
        return idx


class CapnProtoCompiler:
    """This class is responsible for taking the metadata and rendering a valid capnproto schema. It also
    would eventually be responsible for maintaining the backwards compatibility of the schema that would
    require it to name fields consistently so that it could look up the indices of the fields and types in
    the existing schema while creating the new version.
    """

    async def compile(self, message: CapnProtoMessageMetadata):
        if message.is_enum:
            async for part in self.compile_enum(message):
                yield part
        else:
            async for part in self.compile_message(message):
                yield part

    async def compile_enum(
        self, message: CapnProtoMessageMetadata
    ) -> AsyncGenerator[CapnProtoEnumRenderer, None]:
        serializer = cast(EnumSerializer[Enum], message.serializer)
        indexer = CapnProtoFieldIndexer()
        yield CapnProtoEnumRenderer(
            serializer.storage_name or serializer.klass.__name__,
            {member.name: indexer.get_idx() for member in message.fields},
        )

    async def compile_message(
        self, message: CapnProtoMessageMetadata
    ) -> AsyncGenerator[
        Union[CapnProtoStructRenderer, CapnProtoUnionRenderer, CapnProtoFieldRenderer], None
    ]:
        serializer = cast(ObjectSerializer[Any], message.serializer)
        indexer = CapnProtoFieldIndexer()
        for field in message.fields:
            async for part in self.compile_field(serializer, indexer, field):
                yield part

    async def compile_field(
        self,
        serializer: ObjectSerializer[Any],
        indexer: CapnProtoFieldIndexer,
        field: CapnProtoFieldMetadata,
    ) -> AsyncGenerator[
        Union[CapnProtoStructRenderer, CapnProtoUnionRenderer, CapnProtoFieldRenderer], None
    ]:
        if isinstance(field.type_, CapnProtoStructMetadata):
            field_idx = indexer.get_idx()
            field_name = serializer.storage_field_names.get(field.name, field.name)
            struct_name = f"{serializer.get_storage_name()}_{field_name}_Tuple"

            indexed_fields = []
            inner_indexer = CapnProtoFieldIndexer()
            for inner_field in field.type_.fields:
                idx = inner_indexer.get_idx()
                inner_prefix = f"{struct_name}_{idx}"
                async for part in self.compile_inner_struct(serializer, inner_prefix, inner_field):
                    yield part
                indexed_fields.append(CapnProtoFieldRenderer(field_name, idx, inner_field))
            yield CapnProtoStructRenderer(struct_name, indexed_fields)
            yield CapnProtoFieldRenderer(field_name, field_idx, struct_name)
        elif isinstance(field.type_, CapnProtoUnionMetadata):
            field_name = serializer.storage_field_names.get(field.name, field.name)
            union_name = f"{serializer.get_storage_name()}_{field.name}_Union"

            indexed_fields = []
            for inner_field in field.type_.fields:
                inner_idx = indexer.get_idx()
                inner_field_name = f"{union_name}_{inner_idx}"
                async for part in self.compile_inner_struct(
                    serializer, inner_field_name, inner_field
                ):
                    yield part
                indexed_fields.append(
                    CapnProtoFieldRenderer(inner_field_name, inner_idx, inner_field)
                )
            yield CapnProtoUnionRenderer(field_name, indexed_fields)

    async def compile_inner_struct(
        self,
        serializer: ObjectSerializer[Any],
        prefix: str,
        field: CapnProtoFieldType,
    ) -> AsyncGenerator[CapnProtoStructRenderer, None]:
        if isinstance(field, CapnProtoStructMetadata) or isinstance(field, CapnProtoUnionMetadata):
            indexed_fields = []
            inner_indexer = CapnProtoFieldIndexer()
            for inner_field in field.fields:
                idx = inner_indexer.get_idx()
                field_name = f"{prefix}_{idx}"
                async for part in self.compile_inner_struct(serializer, field_name, inner_field):
                    yield part
                indexed_fields.append(CapnProtoFieldRenderer(field_name, idx, inner_field))
            if isinstance(field, CapnProtoUnionMetadata):
                # A nested union is a struct in capnproto. Unions aren't first-class abstractions but just groups of fields.
                yield CapnProtoStructRenderer(
                    prefix, [CapnProtoUnionRenderer(None, indexed_fields)]
                )
            else:
                yield CapnProtoStructRenderer(prefix, indexed_fields)
