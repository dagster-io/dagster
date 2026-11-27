import logging
import sys
import weakref
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING, AbstractSet, Generic, Mapping, Union  # noqa: UP035

from typing_extensions import Protocol, TypeVar, runtime_checkable

import dagster._check as check
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.log_manager import get_log_record_metadata
from dagster._core.types.pagination import PaginatedResults
from dagster._record import record
from dagster._utils.cached_method import cached_method
from dagster._utils.error import serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from dagster._core.definitions.dynamic_partitions_request import (
        AddDynamicPartitionsRequest,
        DeleteDynamicPartitionsRequest,
    )
    from dagster._core.instance.instance import DagsterInstance


class _EventListenerLogHandler(logging.Handler):
    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        from dagster._core.events import EngineEventData
        from dagster._core.events.log import StructuredLoggerMessage, construct_event_record

        record_metadata = get_log_record_metadata(record)
        event = construct_event_record(
            StructuredLoggerMessage(
                name=record.name,
                message=record.msg,
                level=record.levelno,
                meta=record_metadata,
                record=record,
            )
        )

        try:
            self._instance.handle_new_event(
                event, batch_metadata=record_metadata["dagster_event_batch_metadata"]
            )
        except Exception as e:
            sys.stderr.write(f"Exception while writing logger call to event log: {e}\n")
            if event.dagster_event:
                # Swallow user-generated log failures so that the entire step/run doesn't fail, but
                # raise failures writing system-generated log events since they are the source of
                # truth for the state of the run
                raise
            elif event.run_id:
                self._instance.report_engine_event(
                    "Exception while writing logger call to event log",
                    job_name=event.job_name,
                    run_id=event.run_id,
                    step_key=event.step_key,
                    engine_event_data=EngineEventData(
                        error=serializable_error_info_from_exc_info(sys.exc_info()),
                    ),
                )


class InstanceType(Enum):
    PERSISTENT = "PERSISTENT"
    EPHEMERAL = "EPHEMERAL"


T_DagsterInstance = TypeVar("T_DagsterInstance", bound="DagsterInstance", default="DagsterInstance")


class MayHaveInstanceWeakref(Generic[T_DagsterInstance]):
    """Mixin for classes that can have a weakref back to a Dagster instance."""

    _instance_weakref: "weakref.ReferenceType[T_DagsterInstance] | None"

    def __init__(self):
        self._instance_weakref = None

    @property
    def has_instance(self) -> bool:
        return hasattr(self, "_instance_weakref") and (self._instance_weakref is not None)

    @property
    def _instance(self) -> T_DagsterInstance:
        instance = (
            self._instance_weakref()
            # Backcompat with custom subclasses that don't call super().__init__()
            # in their own __init__ implementations
            if (hasattr(self, "_instance_weakref") and self._instance_weakref is not None)
            else None
        )
        if instance is None:
            raise DagsterInvariantViolationError(
                "Attempted to resolve undefined DagsterInstance weakref."
            )
        else:
            return instance

    def register_instance(self, instance: T_DagsterInstance) -> None:
        check.invariant(
            (
                # Backcompat with custom subclasses that don't call super().__init__()
                # in their own __init__ implementations
                not hasattr(self, "_instance_weakref") or self._instance_weakref is None
            ),
            "Must only call initialize once",
        )

        # Store a weakref to avoid a circular reference / enable GC
        self._instance_weakref = weakref.ref(instance)


@runtime_checkable
class DynamicPartitionsStore(Protocol):
    @abstractmethod
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]: ...

    @abstractmethod
    def get_paginated_dynamic_partitions(
        self,
        partitions_def_name: str,
        limit: int,
        ascending: bool,
        cursor: str | None = None,
    ) -> PaginatedResults[str]: ...

    @abstractmethod
    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool: ...

    def get_existing_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> AbstractSet[str]:
        """Return the subset of ``partition_keys`` that exist in the partitions definition.

        Stores that can answer this with a bounded query should override; the default loads the
        full key set.
        """
        return set(self.get_dynamic_partitions(partitions_def_name)) & set(partition_keys)

    @abstractmethod
    def get_dynamic_partitions_definition_id(self, partitions_def_name: str) -> str: ...


class CachingDynamicPartitionsLoader(DynamicPartitionsStore):
    """A batch loader that caches the partition keys for a given dynamic partitions definition,
    to avoid repeated calls to the database for the same partitions definition.
    """

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance
        self._existence_by_partitions_def_name: dict[str, dict[str, bool]] = defaultdict(dict)

    @cached_method
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        return self._instance.get_dynamic_partitions(partitions_def_name)

    @cached_method
    def get_paginated_dynamic_partitions(
        self, partitions_def_name: str, limit: int, ascending: bool, cursor: str | None = None
    ) -> PaginatedResults[str]:
        return self._instance.get_paginated_dynamic_partitions(
            partitions_def_name=partitions_def_name, limit=limit, ascending=ascending, cursor=cursor
        )

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        # A single key goes to the single-key query, which every storage answers with an indexed
        # lookup. Routing it through the batched form would make storages that have no bounded
        # batch query load the whole definition to check one key.
        existence = self._existence_by_partitions_def_name[partitions_def_name]
        if partition_key not in existence:
            existence[partition_key] = self._instance.has_dynamic_partition(
                partitions_def_name, partition_key
            )
        return existence[partition_key]

    def get_existing_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> AbstractSet[str]:
        existence = self._existence_by_partitions_def_name[partitions_def_name]
        unknown = [pk for pk in partition_keys if pk not in existence]
        if unknown:
            if self._instance.event_log_storage.has_bounded_dynamic_partition_membership_query:
                existing = self._instance.get_existing_dynamic_partitions(
                    partitions_def_name, unknown
                )
            else:
                # The storage would load the whole definition for each batch, so load it once
                # through the cached accessor and answer every later batch from it.
                existing = set(self.get_dynamic_partitions(partitions_def_name))
            for pk in unknown:
                existence[pk] = pk in existing
        return {pk for pk in partition_keys if existence[pk]}

    @cached_method
    def get_dynamic_partitions_definition_id(self, partitions_def_name: str) -> str:
        return self._instance.get_dynamic_partitions_definition_id(partitions_def_name)


@record
class DynamicPartitionsStoreAfterRequests(DynamicPartitionsStore):
    """Represents the dynamic partitions that will be in the contained DynamicPartitionsStore
    after the contained requests are satisfied.
    """

    wrapped_dynamic_partitions_store: DynamicPartitionsStore
    added_partition_keys_by_partitions_def_name: Mapping[str, AbstractSet[str]]
    deleted_partition_keys_by_partitions_def_name: Mapping[str, AbstractSet[str]]

    @staticmethod
    def from_requests(
        wrapped_dynamic_partitions_store: DynamicPartitionsStore,
        dynamic_partitions_requests: Sequence[
            Union["AddDynamicPartitionsRequest", "DeleteDynamicPartitionsRequest"]
        ],
    ) -> "DynamicPartitionsStoreAfterRequests":
        from dagster._core.definitions.dynamic_partitions_request import (
            AddDynamicPartitionsRequest,
            DeleteDynamicPartitionsRequest,
        )

        added_partition_keys_by_partitions_def_name: dict[str, set[str]] = defaultdict(set)
        deleted_partition_keys_by_partitions_def_name: dict[str, set[str]] = defaultdict(set)

        for req in dynamic_partitions_requests:
            name = req.partitions_def_name
            if isinstance(req, AddDynamicPartitionsRequest):
                added_partition_keys_by_partitions_def_name[name].update(set(req.partition_keys))
            elif isinstance(req, DeleteDynamicPartitionsRequest):
                deleted_partition_keys_by_partitions_def_name[name].update(set(req.partition_keys))
            else:
                check.failed(f"Unexpected request type: {req}")

        return DynamicPartitionsStoreAfterRequests(
            wrapped_dynamic_partitions_store=wrapped_dynamic_partitions_store,
            added_partition_keys_by_partitions_def_name=added_partition_keys_by_partitions_def_name,
            deleted_partition_keys_by_partitions_def_name=deleted_partition_keys_by_partitions_def_name,
        )

    @cached_method
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        partition_keys = set(
            self.wrapped_dynamic_partitions_store.get_dynamic_partitions(partitions_def_name)
        )
        added_partition_keys = self.added_partition_keys_by_partitions_def_name.get(
            partitions_def_name, set()
        )
        deleted_partition_keys = self.deleted_partition_keys_by_partitions_def_name.get(
            partitions_def_name, set()
        )
        return list((partition_keys | added_partition_keys) - deleted_partition_keys)

    @cached_method
    def get_paginated_dynamic_partitions(
        self, partitions_def_name: str, limit: int, ascending: bool, cursor: str | None = None
    ) -> PaginatedResults[str]:
        partition_keys = self.get_dynamic_partitions(partitions_def_name)
        return PaginatedResults.create_from_sequence(
            seq=partition_keys, limit=limit, ascending=ascending, cursor=cursor
        )

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        deleted = self.deleted_partition_keys_by_partitions_def_name.get(partitions_def_name, set())
        added = self.added_partition_keys_by_partitions_def_name.get(partitions_def_name, set())
        return partition_key not in deleted and (
            partition_key in added
            or self.wrapped_dynamic_partitions_store.has_dynamic_partition(
                partitions_def_name, partition_key
            )
        )

    def get_existing_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> AbstractSet[str]:
        deleted = self.deleted_partition_keys_by_partitions_def_name.get(partitions_def_name, set())
        added = self.added_partition_keys_by_partitions_def_name.get(partitions_def_name, set())
        candidates = [pk for pk in partition_keys if pk not in deleted]
        unresolved = [pk for pk in candidates if pk not in added]
        existing = (
            self.wrapped_dynamic_partitions_store.get_existing_dynamic_partitions(
                partitions_def_name, unresolved
            )
            if unresolved
            else set()
        )
        return {pk for pk in candidates if pk in added or pk in existing}

    def get_dynamic_partitions_definition_id(self, partitions_def_name: str) -> str:
        return self.wrapped_dynamic_partitions_store.get_dynamic_partitions_definition_id(
            partitions_def_name
        )
