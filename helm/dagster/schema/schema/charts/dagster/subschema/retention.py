from pydantic import BaseModel, Extra
from typing import Any, Dict, List, Optional, Union


class TickRetentionByType(BaseModel):
    skipped: Optional[int]
    success: Optional[int]
    failure: Optional[int]
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
