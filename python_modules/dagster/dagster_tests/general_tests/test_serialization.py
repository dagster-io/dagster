import dataclasses
import logging
from abc import ABC, abstractmethod
from asyncio import Future, TimeoutError, gather, wait_for
from collections import defaultdict
from contextlib import asynccontextmanager
from enum import Enum
from inspect import Parameter, signature
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    ForwardRef,
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
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

import dagster._check as check
import pydantic
import pytest
from dagster._model.pydantic_compat_layer import model_fields
from dagster._record import IHaveNew, get_record_annotations, has_generated_new
from dagster._serdes.serdes import _WHITELIST_MAP
from dagster._utils import is_named_tuple_subclass

logger = logging.getLogger(__name__)



TTypeMetadata = TypeVar("TTypeMetadata")
class BaseScribe(Generic[TTypeMetadata], ABC):
    class BaseScribeContext(ABC):
        def __init__(self):
            self._fields = []

        def add_field(self, name: str, type_: Type[Any], field_str: str):
            self._fields.append((name, type_, field_str))

    _scribed_types: Dict[Type[Any], Future[TTypeMetadata]] = defaultdict(Future)

    @asynccontextmanager
    @abstractmethod
    def new_type_context(self, type_: Type[Any]) -> AsyncGenerator[BaseScribeContext, None]:
        pass

    @abstractmethod
    async def from_field(self, ctx: BaseScribeContext, name: str, type_: Type[Any]) -> None:
        pass

    def insert_scribed_type(self, type_: Type[Any], scribed_type: TTypeMetadata) -> None:
        self._scribed_types[type_].set_result(scribed_type)

    async def get_scribed_type(self, type_: Type[Any]) -> TTypeMetadata:
        return await self._scribed_types[type_]

    async def from_record(self, klazz: Type[IHaveNew]):
        async with self.new_type_context(klazz) as ctx:
            for name, type_ in get_record_annotations(klazz).items():
                await self.from_field(ctx, name, type(type_))

    async def from_named_tuple(self, klazz: Type[NamedTuple]):
        if has_generated_new(klazz):
            await self.from_record(cast(Type[IHaveNew], klazz))
            return

        # Skip past the first parameter, which is the cls
        params = iter(signature(klazz.__new__).parameters.items())
        should_be_cls = next(params)[0]
        assert (
            "cls" in should_be_cls
        ), f"First parameter of __new__ should be cls, got {should_be_cls}"

        async with self.new_type_context(klazz) as ctx:
            kwargs_fields = []
            for name, parameter in params:
                if parameter.kind is Parameter.VAR_POSITIONAL:
                    check.failed("Can not use positional args capture on serdes object.")
                elif parameter.kind is Parameter.VAR_KEYWORD:
                    kwargs_fields.append((name, parameter))
                else:
                    if not isinstance(parameter.annotation, type) and get_origin(parameter.annotation) is None:
                        raise Exception(f"Field {parameter.name} on {klazz.__name__} is not a type got {parameter.annotation} which is {type(parameter.annotation)}")
                    await self.from_field(ctx, name, cast(Type[Any], parameter.annotation))
            if kwargs_fields:
                # add kwargs field
                pass

    async def from_pydantic(self, klazz: Type[pydantic.BaseModel]):
        async with self.new_type_context(klazz) as ctx:
            for name, field in model_fields(klazz).items():
                await self.from_field(ctx, name, field.annotation)

    async def from_dataclass(self, klazz: Type[Any]):
        async with self.new_type_context(klazz) as ctx:
            for field in dataclasses.fields(klazz):
                if not isinstance(field.type, type) and get_origin(field.type) is None:
                    raise Exception(f"Field {field.name} on {klazz.__name__} is not a type got {field.type} which is {type(field.type)}")
                await self.from_field(ctx, field.name, field.type)

    async def from_enum(self, klazz: Type[Enum]):
        pass

    async def from_class(self, klazz: Type[Any]):
        if dataclasses.is_dataclass(klazz):
            await self.from_dataclass(klazz)
        elif is_named_tuple_subclass(klazz):
            await self.from_named_tuple(klazz)
        elif issubclass(klazz, Enum):
            await self.from_enum(klazz)
        elif issubclass(klazz, pydantic.BaseModel):
            await self.from_pydantic(klazz)


class CapnProtoMetadata(NamedTuple):
    storage_name: str
    struct_string: str


class CapnProtoScribe(BaseScribe[CapnProtoMetadata]):
    class CapnProtoScribeContext(BaseScribe.BaseScribeContext):
        """Context is object-level context for the field scribing function to use.
        This is useful for protocol level logic, such as tracking the index of the fields.
        This is also responsible for building the metadata, but not responsible for string formatting.
        """

        def __init__(self):
            super().__init__()

        def get_field_index(self, name: str) -> int:
            # TODO: look up the index of an existing field
            return len(self._fields)

    @asynccontextmanager
    async def new_type_context(
        self, type_: Type[Any]
    ) -> AsyncGenerator[CapnProtoScribeContext, None]:
        ctx = CapnProtoScribe.CapnProtoScribeContext()
        yield ctx

        storage_name = type_.__name__

        struct_decl = f"struct {storage_name}"
        indent = "    "
        block = "\n".join(
            [
                "{",
                *(indent + decl for _name, _type, decl in ctx._fields),
                "};",
            ]
        )

        metadata = CapnProtoMetadata(storage_name, struct_decl + block)
        self.insert_scribed_type(type_, metadata)

    def _is_optional(self, type_: Type[Any]) -> bool:
        if get_origin(type_) is Union:
            args = get_args(type_)
            return type(None) in args and len(args) == 2
        return False

    def _unwrap_type(self, type_: Type[Any]) -> Type[Any]:
        # Optional[Optional[Optional[int]]] -> int
        while self._is_optional(type_):
            # get the non-None type from the Union
            type_ = next((t for t in get_args(type_) if t is not type(None)))

        return type_

    async def scribe_type(self, type_: Type[Any]) -> str:
        type_ = self._unwrap_type(type_)

        # We need un-annotated types for issubclass checks
        args = get_args(type_)
        if get_origin(type_) is not None:
            type_ = cast(Type, get_origin(type_))

        if type_ is str:
            return "Text"
        elif type_ is int:
            return "Int64"
        elif type_ is float:
            return "Float64"
        elif type_ is bool:
            return "Bool"
        elif issubclass(type_, Mapping):
            key_str = "AnyPointer"
            value_str = "AnyPointer"
            if args:
                key_type, value_type = args
                key_str, value_str = await gather(
                    self.scribe_type(key_type),
                    self.scribe_type(value_type),
                )
            # TODO: need to actually write the map type and mapping type
            # TODO: we need packing logic to make sure that int and float keys are packed, unpacked thru text
            return f"Mapping({key_str}, {value_str})"
        elif issubclass(type_, Set):
            # TODO: need to actually write the set type
            inner_type = "AnyPointer"
            if args:
                inner_type = await self.scribe_type(args[0])
            return f"Set({inner_type})"
        elif issubclass(type_, FrozenSet):
            # TODO: need to actually write the frozenset type
            inner_type = "AnyPointer"
            if args:
                inner_type = await self.scribe_type(args[0])
            return f"FrozenSet({inner_type})"
        elif issubclass(type_, List):
            # includes List, Tuple, and Deque
            inner_type = "AnyPointer"
            if args:
                inner_type = await self.scribe_type(args[0])
            return f"List({inner_type})"
        elif issubclass(type_, Tuple):
            # TODO: needs to be group of fields
            return "AnyPointer"
        elif issubclass(type_, Sequence):
            # TODO: needs to be union of List or AnyPointer
            inner_type = "AnyPointer"
            if args:
                inner_type = await self.scribe_type(args[0])
            return f"Sequence({inner_type})"
        elif get_origin(type_) is Union:
            # TODO: use ctx to create a side effect inside struct to encapsulate the union
            # inner_struct = ctx.create_union_struct(name, args)
            # return inner_struct
            return "AnyPointer"
        else:
            metadata = await self.get_scribed_type(type_)
            return f"{metadata.struct_string}"

    async def from_field(self, ctx: CapnProtoScribeContext, name: str, type_: Type[Any]):
        type_str = await self.scribe_type(type_)
        idx = ctx.get_field_index(name)

        ctx.add_field(name, type_, f"{name} @{idx} {type_str};")


@pytest.mark.asyncio
async def test_generate_protobuf_from_class():
    scribe = CapnProtoScribe()
    scribe_tasks = [
        scribe.from_class(serializer.klass)
        for serializer in _WHITELIST_MAP.object_serializers.values()
    ]

    try:
        await wait_for(gather(*scribe_tasks), timeout=10)
    except TimeoutError:
        unresolved = [type_ for type_, future in scribe._scribed_types.items() if not future.done()]
        print(f"Unresolved types: {unresolved}")

    print("Done")
