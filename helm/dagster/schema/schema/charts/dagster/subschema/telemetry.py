from pydantic import Extra, BaseModel


class Telemetry(BaseModel):
    enabled: bool

    class Config:
        extra = Extra.forbid
