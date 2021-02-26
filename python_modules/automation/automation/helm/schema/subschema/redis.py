from pydantic import BaseModel, Extra  # pylint: disable=E0611


class Redis(BaseModel):
    enabled: bool
    host: str
    port: int
    brokerDbNumber: int
    backendDbNumber: int

    class Config:
        extra = Extra.allow
