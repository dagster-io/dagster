from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils.kubernetes import ExternalImage


class Service(BaseModel):
    port: int


class PostgreSQL(BaseModel):
    image: ExternalImage
    enabled: bool
    postgresqlHost: str
    postgresqlUsername: str
    postgresqlPassword: str
    postgresqlDatabase: str
    postgresqlParams: dict
    service: Service
