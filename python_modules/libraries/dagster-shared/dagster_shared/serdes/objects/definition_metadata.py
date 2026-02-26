from collections.abc import Mapping, Sequence
from typing import Any

from dagster_shared.record import as_dict, record


@record
class DgAssetMetadata:
    key: str
    deps: list[str]
    kinds: list[str]
    group: str | None
    description: str | None
    automation_condition: str | None
    tags: Sequence[str]
    is_executable: bool
    source: str | None
    owners: Sequence[str] | None


@record
class DgSensorMetadata:
    name: str
    source: str | None


@record
class DgScheduleMetadata:
    name: str
    cron_schedule: str
    source: str | None


@record
class DgJobMetadata:
    name: str
    description: str | None
    source: str | None


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
    description: str | None
    source: str | None


@record
class DgDefinitionMetadata:
    assets: list[DgAssetMetadata]
    asset_checks: list[DgAssetCheckMetadata]
    jobs: list[DgJobMetadata]
    resources: list[DgResourceMetadata]
    schedules: list[DgScheduleMetadata]
    sensors: list[DgSensorMetadata]

    def to_dict(self) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        return {
            "assets": [as_dict(asset) for asset in self.assets],
            "asset_checks": [as_dict(asset_check) for asset_check in self.asset_checks],
            "jobs": [as_dict(job) for job in self.jobs],
            "resources": [as_dict(resource) for resource in self.resources],
            "schedules": [as_dict(schedule) for schedule in self.schedules],
            "sensors": [as_dict(sensor) for sensor in self.sensors],
        }

    @property
    def is_empty(self) -> bool:
        return (
            not self.assets
            and not self.asset_checks
            and not self.jobs
            and not self.resources
            and not self.schedules
            and not self.sensors
        )
