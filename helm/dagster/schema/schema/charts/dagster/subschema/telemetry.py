from pydantic import BaseModel, Extra  # pylint: disable=no-name-in-module


class Telemetry(BaseModel):
    enabled: bool

    class Config:
        extra = Extra.forbid
