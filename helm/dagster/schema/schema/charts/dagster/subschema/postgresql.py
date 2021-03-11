from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils.kubernetes import ImageWithRegistry


class Service(BaseModel):
    port: int


class PostgreSQL(BaseModel):
    image: ImageWithRegistry
    enabled: bool
    postgresqlHost: str
    postgresqlUsername: str
    postgresqlPassword: str
    postgresqlDatabase: str
    service: Service
