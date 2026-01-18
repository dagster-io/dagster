from typing import Optional, Union

from pydantic import BaseModel


class TickRetentionByType(BaseModel, extra="forbid"):
    skipped: int
    success: int
    failure: int
    started: int


class TickRetention(BaseModel):
    purgeAfterDays: Union[int, TickRetentionByType]


class Retention(BaseModel, extra="forbid"):
    enabled: bool
    sensor: TickRetention
    schedule: TickRetention
    autoMaterialize: Optional[TickRetention] = None
