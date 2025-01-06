from enum import Enum
from typing import Any, AsyncGenerator, Generator, List, NamedTuple, Optional, Union, cast

from dagster._serdes.serdes import EnumSerializer, ObjectSerializer
from dagster._serialization.capnproto.types import (
    CapnProtoCollectionType,
    CapnProtoFieldMetadata,
    CapnProtoFieldType,
    CapnProtoMessageMetadata,
    CapnProtoStructMetadata,
    CapnProtoUnionMetadata,
)

TAB = "  "


class CapnProtoEnumRenderer(NamedTuple):
    name: str
    members: dict[str, int]

    def render(self, indent: str) -> Generator[str, None, None]:
        yield f"{indent}enum {self.name} {{"
        for member, idx in self.members.items():
            yield f"{indent}{TAB}{member} @{idx};"
        yield f"{indent}}}"


class CapnProtoFieldRenderer(NamedTuple):
    name: str
    idx: int
    type_: str

    def render(self, indent: str) -> Generator[str, None, None]:
        yield f"{indent}@{self.idx} {self.name} :{self.type_};"


class CapnProtoUnionRenderer(NamedTuple):
    name: Optional[str]
    fields: List[CapnProtoFieldRenderer]

    def render(self, indent: str = "  ") -> Generator[str, None, None]:
        name = self.name or ""
        yield f"{indent}union {name} {{"
        for field in self.fields:
            yield from field.render(indent + TAB)
        yield f"{indent}}}"


class CapnProtoStructRenderer(NamedTuple):
    name: str
    structs: List["CapnProtoStructRenderer"]
    fields: List[Union[CapnProtoFieldRenderer, CapnProtoUnionRenderer]]

    def render(self, indent: str = "  ") -> Generator[str, None, None]:
        yield f"{indent}struct {self.name} {{"
        for struct in self.structs:
            yield from struct.render(indent + TAB)
        for field in self.fields:
            yield from field.render(indent + TAB)
        yield f"{indent}}}"


class CapnProtoFieldIndexer:
    """This class would eventually be able to bridge the indexings of the fields between schema versions."""

    def __init__(self):
        self._idx = 0

    def get_idx(self) -> int:
        # TODO: should look up existing idx in the capnproto schema to do backcompat stuff
        idx = self._idx
        self._idx += 1
        return idx


class CapnProtoCompiler:
    """This class is responsible for taking the metadata and rendering a valid capnproto schema. It also
    would eventually be responsible for maintaining the backwards compatibility of the schema that would
    require it to name fields consistently so that it could look up the indices of the fields and types in
    the existing schema while creating the new version.
    """

    async def compile(self, message: CapnProtoMessageMetadata):
        if message.is_enum:
            return await self.compile_enum(message)
        else:
            return await self.compile_message(message)

    async def compile_enum(self, message: CapnProtoMessageMetadata) -> CapnProtoEnumRenderer:
        serializer = cast(EnumSerializer[Enum], message.serializer)
        indexer = CapnProtoFieldIndexer()
        return CapnProtoEnumRenderer(
            serializer.get_storage_name(),
            {member.name: indexer.get_idx() for member in message.fields},
        )

    async def compile_message(self, message: CapnProtoMessageMetadata) -> CapnProtoStructRenderer:
        serializer = cast(ObjectSerializer[Any], message.serializer)
        indexer = CapnProtoFieldIndexer()

        inner_structs = []
        fields_and_unions = []
        for field in message.fields:
            field_name = serializer.storage_field_names.get(field.name, field.name)
            async for part in self.compile_field(
                field_name, indexer.get_idx(), field.type_, indexer, is_root_field=True
            ):
                if isinstance(part, CapnProtoStructRenderer):
                    inner_structs.append(part)
                else:
                    fields_and_unions.append(part)
        return CapnProtoStructRenderer(
            serializer.get_storage_name(), inner_structs, fields_and_unions
        )

    async def compile_field(
        self,
        field_name: str,
        field_idx: int,
        field_type: CapnProtoFieldType,
        indexer: CapnProtoFieldIndexer,
        is_root_field: bool = False,
    ) -> AsyncGenerator[
        Union[CapnProtoStructRenderer, CapnProtoUnionRenderer, CapnProtoFieldRenderer], None
    ]:
        if isinstance(field_type, CapnProtoStructMetadata):
            field_type = cast(CapnProtoStructMetadata[CapnProtoFieldType], field_type)
            inner_fields = []
            inner_indexer = CapnProtoFieldIndexer()
            for inner_field in field_type.fields:
                inner_idx = inner_indexer.get_idx()
                async for part in self.compile_field(
                    f"{field_name}_{inner_idx}",
                    inner_idx,
                    inner_field,
                    inner_indexer
                ):
                    if isinstance(part, CapnProtoFieldRenderer):
                        inner_fields.append(part)
                    else:
                        yield part
            yield CapnProtoStructRenderer(field_name, [], inner_fields)
            yield CapnProtoFieldRenderer(field_name, field_idx, field_name)
        elif isinstance(field_type, CapnProtoUnionMetadata):
            field_type = cast(CapnProtoUnionMetadata[CapnProtoFieldType], field_type)
            inner_fields = []
            inner_indexer = indexer if is_root_field else CapnProtoFieldIndexer()
            for inner_field in field_type.fields:
                inner_idx = inner_indexer.get_idx()
                async for part in self.compile_field(
                    f"{field_name}_{inner_idx}",
                    inner_idx,
                    inner_field,
                    inner_indexer
                ):
                    if isinstance(part, CapnProtoFieldRenderer):
                        inner_fields.append(part)
                    else:
                        yield part
            if not is_root_field:
                yield CapnProtoStructRenderer(
                    field_name, [], [CapnProtoUnionRenderer(None, inner_fields)]
                )
                yield CapnProtoFieldRenderer(field_name, field_idx, field_name)
            else:
                yield CapnProtoUnionRenderer(field_name, inner_fields)
        elif isinstance(field_type, CapnProtoCollectionType):
            throw_away_indexer = CapnProtoFieldIndexer()
            async for part in self.compile_field(
                field_name,
                0,
                field_type.generic_arg,
                throw_away_indexer,
            ):
                if isinstance(part, CapnProtoFieldRenderer):
                    type_name = part.type_
                else:
                    yield part
            yield CapnProtoFieldRenderer(field_name, field_idx, type_name)
        elif isinstance(field_type, CapnProtoMessageMetadata):
            inner_serializer = field_type.serializer
            type_name = inner_serializer.get_storage_name()  # type: ignore
            yield CapnProtoFieldRenderer(field_name, field_idx, type_name)
        else:
            yield CapnProtoFieldRenderer(field_name, field_idx, field_type)
