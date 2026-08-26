from typing import Any

from pydantic import BaseModel

from dagster_rest_resources.__generated__.enums import ReportingTimeRange, ReportingUnitType
from dagster_rest_resources.schemas.util import DgApiList


class DgApiMetricType(BaseModel):
    id: str
    metric_name: str
    display_name: str
    category: str | None = None
    unit_type: ReportingUnitType | None = None
    description: str | None = None
    pending: bool | None = None
    visible: bool | None = None
    custom_icon: str | None = None
    cost_multiplier: float | None = None


class DgApiMetricTypeList(DgApiList[DgApiMetricType]):
    pass


class DgApiMetricValueChange(BaseModel):
    change: float
    is_newly_available: bool


class DgApiMetricEntry(BaseModel):
    """One entity's values for a metric over the requested window.

    `entity` is whichever of asset, asset group, job, deployment or selection the query was
    scoped to, carried through as the object the api returned rather than restated as a
    union here. `values` lines up with the `timestamps` on the enclosing result.
    """

    entity: dict[str, Any]
    aggregate_value: float
    aggregate_value_change: DgApiMetricValueChange
    values: list[float | None]


class DgApiMetrics(BaseModel):
    items: list[DgApiMetricEntry]
    timestamps: list[float]


class DgApiMetricsTimeRanges(DgApiList[ReportingTimeRange]):
    pass
