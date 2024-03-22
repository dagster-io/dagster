from typing import Any

import pydantic
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

    def _replace(self, **kwargs: Any):
        if pydantic.__version__ >= "2":
            func = getattr(BaseModel, "model_copy")
        else:
            func = getattr(BaseModel, "copy")
        return func(self, update=kwargs)
