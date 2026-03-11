"""Pydantic models for `dg list` command JSON output schemas."""

from typing import TYPE_CHECKING

from pydantic import BaseModel

from dagster_dg_cli.api_layer.schemas.asset import DgApiAutomationCondition, DgAssetBase

if TYPE_CHECKING:
    from dagster_shared.serdes.objects.definition_metadata import (
        DgAssetCheckMetadata,
        DgAssetMetadata,
        DgDefinitionMetadata,
        DgJobMetadata,
        DgResourceMetadata,
        DgScheduleMetadata,
        DgSensorMetadata,
    )

# ########################
# ##### COMPONENTS
# ########################


class DgComponentItem(BaseModel):
    """A single component type entry."""

    key: str
    summary: str | None


class DgComponentList(BaseModel):
    """JSON output schema for ``dg list components --json``."""

    items: list[DgComponentItem]


# ########################
# ##### REGISTRY MODULES
# ########################


class DgRegistryModuleItem(BaseModel):
    """A single registry module entry."""

    module: str


class DgRegistryModuleList(BaseModel):
    """JSON output schema for ``dg list registry-modules --json``."""

    items: list[DgRegistryModuleItem]


# ########################
# ##### DEFS
# ########################


class DgDefAssetMetadata(DgAssetBase):
    """Asset metadata from local definitions (extends shared base with local-only fields)."""

    is_executable: bool
    source: str | None = None

    @classmethod
    def from_local_metadata(cls, record: "DgAssetMetadata") -> "DgDefAssetMetadata":
        return cls(
            asset_key=record.asset_key,
            asset_key_parts=record.asset_key.split("/"),
            group_name=record.group_name,
            dependency_keys=record.dependency_keys,
            kinds=record.kinds,
            description=record.description,
            owners=[dict(o) for o in record.owners] if record.owners is not None else None,
            tags=[dict(t) for t in record.tags] if record.tags else None,
            automation_condition=DgApiAutomationCondition(**record.automation_condition)
            if record.automation_condition
            else None,
            is_executable=record.is_executable,
            source=record.source,
        )


class DgDefAssetCheckMetadata(BaseModel):
    key: str
    asset_key: str
    name: str
    additional_deps: list[str]
    description: str | None
    source: str | None

    @classmethod
    def from_local_metadata(cls, record: "DgAssetCheckMetadata") -> "DgDefAssetCheckMetadata":
        return cls(
            key=record.key,
            asset_key=record.asset_key,
            name=record.name,
            additional_deps=record.additional_deps,
            description=record.description,
            source=record.source,
        )


class DgDefJobMetadata(BaseModel):
    name: str
    description: str | None
    source: str | None

    @classmethod
    def from_local_metadata(cls, record: "DgJobMetadata") -> "DgDefJobMetadata":
        return cls(
            name=record.name,
            description=record.description,
            source=record.source,
        )


class DgDefResourceMetadata(BaseModel):
    name: str
    type: str

    @classmethod
    def from_local_metadata(cls, record: "DgResourceMetadata") -> "DgDefResourceMetadata":
        return cls(name=record.name, type=record.type)


class DgDefScheduleMetadata(BaseModel):
    name: str
    cron_schedule: str
    source: str | None

    @classmethod
    def from_local_metadata(cls, record: "DgScheduleMetadata") -> "DgDefScheduleMetadata":
        return cls(
            name=record.name,
            cron_schedule=record.cron_schedule,
            source=record.source,
        )


class DgDefSensorMetadata(BaseModel):
    name: str
    source: str | None

    @classmethod
    def from_local_metadata(cls, record: "DgSensorMetadata") -> "DgDefSensorMetadata":
        return cls(name=record.name, source=record.source)


class DgDefinitionMetadataSchema(BaseModel):
    """JSON output schema for ``dg list defs --json``."""

    assets: list[DgDefAssetMetadata]
    asset_checks: list[DgDefAssetCheckMetadata]
    jobs: list[DgDefJobMetadata]
    resources: list[DgDefResourceMetadata]
    schedules: list[DgDefScheduleMetadata]
    sensors: list[DgDefSensorMetadata]

    @classmethod
    def from_local_definitions(cls, defs: "DgDefinitionMetadata") -> "DgDefinitionMetadataSchema":
        return cls(
            assets=[DgDefAssetMetadata.from_local_metadata(a) for a in defs.assets],
            asset_checks=[
                DgDefAssetCheckMetadata.from_local_metadata(c) for c in defs.asset_checks
            ],
            jobs=[DgDefJobMetadata.from_local_metadata(j) for j in defs.jobs],
            resources=[DgDefResourceMetadata.from_local_metadata(r) for r in defs.resources],
            schedules=[DgDefScheduleMetadata.from_local_metadata(s) for s in defs.schedules],
            sensors=[DgDefSensorMetadata.from_local_metadata(s) for s in defs.sensors],
        )
