from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Extra


class TickRetentionByType(BaseModel):
    skipped: Optional[int]
    success: Optional[int]
    failed: Optional[int]
    started: Optional[int]

    class Config:
        extra = Extra.forbid


class TickRetention(BaseModel):
    purgeAfterDays: Union[int, TickRetentionByType]


class Retention(BaseModel):
    sensor: TickRetention
    schedule: TickRetention

    class Config:
        extra = Extra.forbid
