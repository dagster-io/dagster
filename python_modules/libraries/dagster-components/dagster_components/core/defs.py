from typing import Literal, Optional, TypedDict, Union

from typing_extensions import TypeAlias

DgDefinitionMetadata: TypeAlias = Union[
    "DgAssetMetadata", "DgSensorMetadata", "DgScheduleMetadata", "DgJobMetadata"
]


class DgAssetMetadata(TypedDict):
    type: Literal["asset"]
    key: str
    deps: list[str]
    kinds: list[str]
    group: Optional[str]
    description: Optional[str]
    automation_condition: Optional[str]


class DgSensorMetadata(TypedDict):
    type: Literal["sensor"]
    name: str


class DgScheduleMetadata(TypedDict):
    type: Literal["schedule"]
    name: str
    cron_schedule: str


class DgJobMetadata(TypedDict):
    type: Literal["job"]
    name: str
