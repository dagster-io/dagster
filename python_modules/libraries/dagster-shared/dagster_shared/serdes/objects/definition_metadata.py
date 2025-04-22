from typing import Optional, Union

from typing_extensions import TypeAlias

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class DgAssetMetadata:
    key: str
    deps: list[str]
    kinds: list[str]
    group: Optional[str]
    description: Optional[str]
    automation_condition: Optional[str]


@whitelist_for_serdes
@record
class DgSensorMetadata:
    name: str


@whitelist_for_serdes
@record
class DgScheduleMetadata:
    name: str
    cron_schedule: str


@whitelist_for_serdes
@record
class DgJobMetadata:
    name: str


@whitelist_for_serdes
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
]
