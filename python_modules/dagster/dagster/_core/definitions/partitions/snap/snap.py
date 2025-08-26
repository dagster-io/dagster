"""This module contains data objects meant to be serialized between
host processes and user processes. They should contain no
business logic or clever indexing. Use the classes in external.py
for that.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Optional, Union

from dagster_shared.record import ImportFrom
from typing_extensions import Self

from dagster import _check as check
from dagster._core.definitions.partitions.schedule_type import ScheduleType
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import whitelist_for_serdes
from dagster._time import datetime_from_timestamp

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.definition import (
        DynamicPartitionsDefinition,
        MultiPartitionsDefinition,
        PartitionsDefinition,
        StaticPartitionsDefinition,
        TimeWindowPartitionsDefinition,
    )
    from dagster._core.definitions.timestamp import TimestampWithTimezone


class PartitionsSnap(ABC):
    @classmethod
    def from_def(cls, partitions_def: "PartitionsDefinition") -> "PartitionsSnap":
        from dagster._core.definitions.partitions.definition import (
            DynamicPartitionsDefinition,
            MultiPartitionsDefinition,
            StaticPartitionsDefinition,
            TimeWindowPartitionsDefinition,
        )

        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            return TimeWindowPartitionsSnap.from_def(partitions_def)
        elif isinstance(partitions_def, StaticPartitionsDefinition):
            return StaticPartitionsSnap.from_def(partitions_def)
        elif isinstance(partitions_def, MultiPartitionsDefinition):
            return MultiPartitionsSnap.from_def(partitions_def)
        elif isinstance(partitions_def, DynamicPartitionsDefinition):
            return DynamicPartitionsSnap.from_def(partitions_def)
        else:
            raise DagsterInvalidDefinitionError(
                "Only static, time window, multi-dimensional partitions, and dynamic partitions"
                " definitions with a name parameter are currently supported."
            )

    @abstractmethod
    def get_partitions_definition(self) -> "PartitionsDefinition": ...


@whitelist_for_serdes(storage_name="ExternalTimeWindowPartitionsDefinitionData")
@record
class TimeWindowPartitionsSnap(PartitionsSnap):
    start: float
    timezone: Optional[str]
    fmt: str
    end_offset: int
    end: Optional[float] = None
    cron_schedule: Optional[str] = None
    exclusions: Optional[
        Sequence[
            Union[
                str,
                Annotated[
                    "TimestampWithTimezone", ImportFrom("dagster._core.definitions.timestamp")
                ],
            ]
        ]
    ] = None
    # superseded by cron_schedule, but kept around for backcompat
    schedule_type: Optional[ScheduleType] = None
    # superseded by cron_schedule, but kept around for backcompat
    minute_offset: Optional[int] = None
    # superseded by cron_schedule, but kept around for backcompat
    hour_offset: Optional[int] = None
    # superseded by cron_schedule, but kept around for backcompat
    day_offset: Optional[int] = None

    @classmethod
    def from_def(cls, partitions_def: "TimeWindowPartitionsDefinition") -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        from dagster._core.definitions.partitions.definition import TimeWindowPartitionsDefinition

        check.inst_param(partitions_def, "partitions_def", TimeWindowPartitionsDefinition)
        return cls(
            cron_schedule=partitions_def.cron_schedule,
            start=partitions_def.start.timestamp(),
            end=partitions_def.end.timestamp() if partitions_def.end else None,
            timezone=partitions_def.timezone,
            fmt=partitions_def.fmt,
            end_offset=partitions_def.end_offset,
            exclusions=partitions_def.exclusions if partitions_def.exclusions else None,
        )

    def get_partitions_definition(self):
        from dagster._core.definitions.partitions.definition import TimeWindowPartitionsDefinition

        if self.cron_schedule is not None:
            return TimeWindowPartitionsDefinition(
                cron_schedule=self.cron_schedule,
                start=datetime_from_timestamp(self.start, tz=self.timezone),  # pyright: ignore[reportArgumentType]
                timezone=self.timezone,
                fmt=self.fmt,
                end_offset=self.end_offset,
                end=(datetime_from_timestamp(self.end, tz=self.timezone) if self.end else None),  # pyright: ignore[reportArgumentType]
                exclusions=self.exclusions if self.exclusions else None,
            )
        else:
            # backcompat case
            return TimeWindowPartitionsDefinition(
                schedule_type=self.schedule_type,
                start=datetime_from_timestamp(self.start, tz=self.timezone),  # pyright: ignore[reportArgumentType]
                timezone=self.timezone,
                fmt=self.fmt,
                end_offset=self.end_offset,
                end=(datetime_from_timestamp(self.end, tz=self.timezone) if self.end else None),  # pyright: ignore[reportArgumentType]
                minute_offset=self.minute_offset,
                hour_offset=self.hour_offset,
                day_offset=self.day_offset,
                exclusions=self.exclusions if self.exclusions else None,
            )


def _dedup_partition_keys(keys: Sequence[str]) -> Sequence[str]:
    # Use both a set and a list here to preserve lookup performance in case of large inputs. (We
    # can't just use a set because we need to preserve ordering.)
    seen_keys: set[str] = set()
    new_keys: list[str] = []
    for key in keys:
        if key not in seen_keys:
            new_keys.append(key)
            seen_keys.add(key)
    return new_keys


@whitelist_for_serdes(storage_name="ExternalStaticPartitionsDefinitionData")
@record_custom(checked=False)
class StaticPartitionsSnap(PartitionsSnap, IHaveNew):
    partition_keys: Sequence[str]

    def __new__(cls, partition_keys: Sequence[str]):
        # for back compat reasons we allow str as a Sequence[str] here
        if not isinstance(partition_keys, str):
            check.sequence_param(
                partition_keys,
                "partition_keys",
                of_type=str,
            )

        return super().__new__(
            cls,
            partition_keys=partition_keys,
        )

    @classmethod
    def from_def(cls, partitions_def: "StaticPartitionsDefinition") -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        from dagster._core.definitions.partitions.definition import StaticPartitionsDefinition

        check.inst_param(partitions_def, "partitions_def", StaticPartitionsDefinition)
        return cls(partition_keys=partitions_def.get_partition_keys())

    def get_partitions_definition(self):
        from dagster._core.definitions.partitions.definition import StaticPartitionsDefinition

        # v1.4 made `StaticPartitionsDefinition` error if given duplicate keys. This caused
        # host process errors for users who had not upgraded their user code to 1.4 and had dup
        # keys, since the host process `StaticPartitionsDefinition` would throw an error.
        keys = _dedup_partition_keys(self.partition_keys)
        return StaticPartitionsDefinition(keys)


@whitelist_for_serdes(
    storage_name="ExternalPartitionDimensionDefinition",
    storage_field_names={"partitions": "external_partitions_def_data"},
)
@record
class PartitionDimensionSnap:
    name: str
    partitions: PartitionsSnap


@whitelist_for_serdes(
    storage_name="ExternalMultiPartitionsDefinitionData",
    storage_field_names={"partition_dimensions": "external_partition_dimension_definitions"},
)
@record
class MultiPartitionsSnap(PartitionsSnap):
    partition_dimensions: Sequence[PartitionDimensionSnap]

    @classmethod
    def from_def(cls, partitions_def: "MultiPartitionsDefinition") -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        from dagster._core.definitions.partitions.definition import MultiPartitionsDefinition

        check.inst_param(partitions_def, "partitions_def", MultiPartitionsDefinition)

        return cls(
            partition_dimensions=[
                PartitionDimensionSnap(
                    name=dimension.name,
                    partitions=PartitionsSnap.from_def(dimension.partitions_def),
                )
                for dimension in partitions_def.partitions_defs
            ]
        )

    def get_partitions_definition(self):
        from dagster._core.definitions.partitions.definition import MultiPartitionsDefinition

        return MultiPartitionsDefinition(
            {
                partition_dimension.name: (
                    partition_dimension.partitions.get_partitions_definition()
                )
                for partition_dimension in self.partition_dimensions
            }
        )


@whitelist_for_serdes(storage_name="ExternalDynamicPartitionsDefinitionData")
@record
class DynamicPartitionsSnap(PartitionsSnap):
    name: str

    @classmethod
    def from_def(cls, partitions_def: "DynamicPartitionsDefinition") -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        from dagster._core.definitions.partitions.definition import DynamicPartitionsDefinition

        check.inst_param(partitions_def, "partitions_def", DynamicPartitionsDefinition)
        if partitions_def.name is None:
            raise DagsterInvalidDefinitionError(
                "Dagster does not support dynamic partitions definitions without a name parameter."
            )
        return cls(name=partitions_def.name)

    def get_partitions_definition(self):
        from dagster._core.definitions.partitions.definition import DynamicPartitionsDefinition

        return DynamicPartitionsDefinition(name=self.name)
