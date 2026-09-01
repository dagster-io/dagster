from typing import Literal

from pydantic import BaseModel


class UI(BaseModel, extra="forbid"):
    label: str | None = None
    intent: Literal["none", "primary", "success", "warning", "danger"] | None = None
