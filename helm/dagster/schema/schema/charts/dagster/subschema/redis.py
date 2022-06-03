from pydantic import BaseModel, Extra


class Redis(BaseModel):
    enabled: bool
    internal: bool
    usePassword: bool
    password: str
    host: str
    port: int
    brokerDbNumber: int
    backendDbNumber: int
    brokerUrl: str
    backendUrl: str

    class Config:
        extra = Extra.allow
