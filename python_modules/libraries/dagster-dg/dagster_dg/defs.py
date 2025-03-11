from dataclasses import dataclass
from typing import Literal, Optional, Union

from typing_extensions import TypeAlias

DgDefinitionMetadata: TypeAlias = Union[
    "DgAssetMetadata", "DgSensorMetadata", "DgScheduleMetadata", "DgJobMetadata"
]


@dataclass
class DgAssetMetadata:
    type: Literal["asset"]
    key: str
    group: Optional[str]
    deps: list[str]
    kinds: list[str]
    description: Optional[str]
    automation_condition: Optional[str] = None


@dataclass
class DgSensorMetadata:
    type: Literal["sensor"]
    name: str


@dataclass
class DgScheduleMetadata:
    type: Literal["schedule"]
    name: str
    cron_schedule: str


@dataclass
class DgJobMetadata:
    type: Literal["job"]
    name: str
