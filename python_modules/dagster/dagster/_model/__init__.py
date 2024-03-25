from typing import Any

from pydantic import BaseModel


class DagsterModel(BaseModel):
    """Standardizes on Pydantic settings that are stricter than the default.
    - Frozen, to avoid complexity caused by mutation.
    - extra=forbid, to avoid bugs caused by accidentally constructing with the wrong arguments.
    """

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

    class Config:
        extra = "forbid"
        frozen = True
