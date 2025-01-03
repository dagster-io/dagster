import dataclasses
import logging
from abc import ABC, abstractmethod
from asyncio import Future
from contextlib import asynccontextmanager
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    Generic,
    Iterable,
    List,
    NamedTuple,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

import pydantic

from dagster._config.snap import ConfigEnumValueSnap
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.definitions.partition import PartitionsSubset
from dagster._core.definitions.run_config import RunConfig
from dagster._core.events import EventSpecificData
from dagster._core.execution.context.input import KeyRangeNoPartitionsDefPartitionsSubset
from dagster._core.remote_representation.origin import RemoteJobOrigin
from dagster._model.pydantic_compat_layer import model_fields
from dagster._record import IHaveNew, get_record_annotations, has_generated_new
from dagster._serdes.serdes import (
    _WHITELIST_MAP,
    EnumSerializer,
    JsonSerializableValue,
    ObjectSerializer,
    PackableValue,
)
from dagster._serialization.base.types import assert_is_type
from dagster._utils import is_named_tuple_subclass

logger = logging.getLogger(__name__)


# This map is used to resolve all the ForwardRefs declared in the whitelisted objects, not really
# "serdes" objects, but it's sort of is a serdes object if we find it while walking the tree of types
ALL_REFERENCED_TYPES = {
    **{
        serializer.klass.__name__: serializer.klass
        for serializer in _WHITELIST_MAP.object_serializers.values()
    },
    "RawMetadataValue": RawMetadataValue,
    "PartitionsSubset": PartitionsSubset,
    "EventSpecificData": EventSpecificData,
    "RunConfig": RunConfig,
    "JsonSerializableValue": JsonSerializableValue,
    "PackableValue": PackableValue,
    "AutoMaterializeRule": AutoMaterializeRule,
    "RemoteJobOrigin": RemoteJobOrigin,
    "ConfigEnumValueSnap": ConfigEnumValueSnap,
    "AutomationCondition": AutomationCondition,
    "DataclassInstance": object,
}

# REVIEW: these anomalies that are worth fixing, classes that are technically allowed in
# serdes objects, but aren't actually serializable themselves.
BANISHED_FROM_SERDES = {
    KeyRangeNoPartitionsDefPartitionsSubset,
}


TTypeMetadata = TypeVar("TTypeMetadata")


class ScribeWillCall(Generic[TTypeMetadata], NamedTuple):
    future: Future[TTypeMetadata]
    waiting: List[str]


class BaseScribe(Generic[TTypeMetadata], ABC):
    """The base implementation of this class just handles breaking apart serializers into their fields.
    This is mostly copied from the serdes implementation of a similar thing. Implementations of this class
    will need to handle the specifics of the serialization format they are targeting, mainly translating
    python types into the types of the serialization format and building a schema from that in _scribed_types.

    This class uses a future map to store the results of the scribing process. This also means that all types
    MUST be scribed. For example, if a message (think class) has a field annotated with a type that is not scribed,
    then that field will never resolve. For that reason, it's a good idea to use a timer to check if all types have
    been resolved or not.
    """

    _scribed_types: Dict[Type[Any], ScribeWillCall[TTypeMetadata]] = dict()

    @abstractmethod
    async def visit_message(self, serializer: ObjectSerializer[Any]) -> TTypeMetadata:
        pass

    @abstractmethod
    async def visit_field(self, ctx: TTypeMetadata, name: str, type_: Type[Any]) -> None:
        pass

    @abstractmethod
    async def visit_enum(self, serializer: EnumSerializer[Enum]) -> TTypeMetadata:
        pass

    async def from_serializer(self, serializer: Union[ObjectSerializer[Any], EnumSerializer[Enum]]):
        try:
            if isinstance(serializer, EnumSerializer):
                await self.from_enum(serializer)
                return

            if dataclasses.is_dataclass(serializer.klass):
                await self.from_dataclass(serializer)
            elif is_named_tuple_subclass(serializer.klass):
                await self.from_named_tuple(serializer)
            elif issubclass(serializer.klass, pydantic.BaseModel):
                await self.from_pydantic(serializer)
            else:
                raise Exception(f"Unsupported serializer type {serializer.klass}")
        except Exception:
            logger.exception(f"Error scribing {serializer.klass}")

    def get_will_call(self) -> Iterable[Tuple[Type[Any], ScribeWillCall[TTypeMetadata]]]:
        return self._scribed_types.items()

    def _insert_scribed_type(self, type_: Type[Any], scribed_type: TTypeMetadata) -> None:
        if type_ not in self._scribed_types:
            self._scribed_types[type_] = ScribeWillCall(Future(), [])

        # REVIEW: some enums appear to be double inserted into the whitelist
        if not self._scribed_types[type_].future.done():
            self._scribed_types[type_].future.set_result(scribed_type)

    async def _get_expected_scribed_type(self, type_: Type[Any], waiting: str) -> TTypeMetadata:
        if type_ not in self._scribed_types:
            self._scribed_types[type_] = ScribeWillCall(Future(), [waiting])
        else:
            self._scribed_types[type_].waiting.append(waiting)

        return await self._scribed_types[type_].future

    @asynccontextmanager
    async def _new_enum(
        self, serializer: EnumSerializer[Enum]
    ) -> AsyncGenerator[TTypeMetadata, None]:
        message = await self.visit_enum(serializer)
        yield message
        self._insert_scribed_type(serializer.klass, message)

    @asynccontextmanager
    async def _new_message(
        self, serializer: ObjectSerializer[Any]
    ) -> AsyncGenerator[TTypeMetadata, None]:
        message = await self.visit_message(serializer)
        yield message
        self._insert_scribed_type(serializer.klass, message)

    async def from_record(self, serializer: ObjectSerializer[IHaveNew]):
        async with self._new_message(serializer) as ctx:
            for name, type_ in get_record_annotations(serializer.klass).items():
                try:
                    await self.visit_field(ctx, name, type_)
                except Exception as e:
                    logger.exception(
                        f"Error scribing {serializer.klass.__name__}.{name} with type {type_}"
                    )
                    raise e

    async def from_named_tuple(self, serializer: ObjectSerializer[NamedTuple]):
        if has_generated_new(serializer.klass):
            await self.from_record(cast(ObjectSerializer[IHaveNew], serializer))
            return

        async with self._new_message(serializer) as ctx:
            for name, type_ in get_type_hints(
                serializer.klass.__new__, globalns=ALL_REFERENCED_TYPES
            ).items():
                try:
                    await self.visit_field(ctx, name, type_)
                except Exception as e:
                    logger.exception(
                        f"Error scribing {serializer.klass.__name__}.{name} with type {type_}"
                    )
                    raise e

    async def from_pydantic(self, serializer: ObjectSerializer[pydantic.BaseModel]):
        async with self._new_message(serializer) as ctx:
            for name, field in model_fields(serializer.klass).items():
                try:
                    await self.visit_field(ctx, name, assert_is_type(field.annotation))
                except Exception as e:
                    logger.error(f"Error scribing field {name} on {serializer.klass.__name__}")
                    raise e

    async def from_dataclass(self, serializer: ObjectSerializer[Any]):
        async with self._new_message(serializer) as ctx:
            for field in dataclasses.fields(serializer.klass):
                try:
                    await self.visit_field(ctx, field.name, assert_is_type(field.type))
                except Exception as e:
                    logger.error(
                        f"Error scribing field {field.name} on {serializer.klass.__name__}"
                    )
                    raise e

    async def from_enum(self, serializer: EnumSerializer[Enum]):
        async with self._new_enum(serializer):
            # REVIEW: kind of strange implementation to follow the pattern but whatever.
            pass
