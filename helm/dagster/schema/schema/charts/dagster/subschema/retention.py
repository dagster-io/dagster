from typing import Optional, Union

from pydantic import BaseModel, Extra


class TickRetentionByType(BaseModel):
    skipped: int
    success: int
    failure: int
    started: int

    class Config:
        extra = Extra.forbid


class TickRetention(BaseModel):
    purgeAfterDays: Union[int, TickRetentionByType]


class Retention(BaseModel):
    enabled: bool
    sensor: TickRetention
    schedule: TickRetention
    autoMaterialize: Optional[TickRetention]

    class Config:
        extra = Extra.forbid
