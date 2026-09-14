from pydantic import BaseModel

from schema.charts.utils import kubernetes


class RedisNode(BaseModel, extra="allow"):
    resources: kubernetes.Resources | None = None


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
    master: RedisNode | None = None
    slave: RedisNode | None = None
