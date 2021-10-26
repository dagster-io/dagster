from pydantic import BaseModel, Extra  # pylint: disable=no-name-in-module


class Redis(BaseModel):
    enabled: bool
    internal: bool
    usePassword: bool
    password: str
    host: str
    port: int
    brokerDbNumber: int
    backendDbNumber: int

    class Config:
        extra = Extra.allow
