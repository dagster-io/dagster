from pydantic import BaseModel


class TickRetentionByType(BaseModel, extra="forbid"):
    skipped: int
    success: int
    failure: int
    started: int


class TickRetention(BaseModel):
    purgeAfterDays: int | TickRetentionByType


class Retention(BaseModel, extra="forbid"):
    enabled: bool
    sensor: TickRetention
    schedule: TickRetention
    autoMaterialize: TickRetention | None = None
