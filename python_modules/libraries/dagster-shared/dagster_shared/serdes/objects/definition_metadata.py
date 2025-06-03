from collections.abc import Sequence
from typing import Optional, Union

from typing_extensions import TypeAlias

from dagster_shared.record import record


@record
class DgAssetMetadata:
    key: str
    deps: list[str]
    kinds: list[str]
    group: Optional[str]
    description: Optional[str]
    automation_condition: Optional[str]
    tags: Sequence[tuple[str, str]]
    metadata: Sequence[tuple[str, str]]


@record
class DgSensorMetadata:
    name: str


@record
class DgScheduleMetadata:
    name: str
    cron_schedule: str


@record
class DgJobMetadata:
    name: str
    description: Optional[str]


@record
class DgResourceMetadata:
    name: str
    type: str


@record
class DgAssetCheckMetadata:
    key: str
    asset_key: str
    name: str
    additional_deps: list[str]
    description: Optional[str]


DgDefinitionMetadata: TypeAlias = Union[
    DgAssetMetadata,
    DgSensorMetadata,
    DgScheduleMetadata,
    DgJobMetadata,
    DgAssetCheckMetadata,
    DgResourceMetadata,
]
