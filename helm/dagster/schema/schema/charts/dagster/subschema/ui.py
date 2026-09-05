from typing import Literal

from pydantic import BaseModel

from schema.charts.dagster.subschema.config import StringSource


class UI(BaseModel, extra="forbid"):
    label: StringSource | None = None
    intent: Literal["none", "primary", "success", "warning", "danger"] | None = None
