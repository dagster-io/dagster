from typing import Literal

from pydantic import BaseModel

from schema.charts.dagster.subschema.config import Source, StringSource


class UI(BaseModel, extra="forbid"):
    label: StringSource | None = None
    # Literal rather than StringSource keeps the enum check for inline values; Source
    # still allows one values file to pick the color per environment.
    intent: Literal["none", "primary", "success", "warning", "danger"] | Source | None = None
