from pydantic import BaseModel


class Telemetry(BaseModel, extra="forbid"):
    enabled: bool
