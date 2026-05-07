from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiInstigationStatus, DgApiSensorType
from dagster_rest_resources.schemas.util import DgApiList


class DgApiSensor(BaseModel):
    id: str
    name: str
    status: DgApiInstigationStatus
    sensor_type: DgApiSensorType
    repository_origin: str
    description: str | None = None
    next_tick_timestamp: float | None = None

    class Config:
        from_attributes = True


class DgApiSensorList(DgApiList["DgApiSensor"]):
    pass
