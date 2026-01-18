from pydantic import BaseModel


class Redis(BaseModel, extra="allow"):
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
