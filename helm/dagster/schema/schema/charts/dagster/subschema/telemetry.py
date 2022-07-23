from pydantic import BaseModel, Extra


class Telemetry(BaseModel):
    enabled: bool

    class Config:
        extra = Extra.forbid
