from pydantic import BaseModel  # pylint: disable=E0611

from .kubernetes import Image


class Service(BaseModel):
    port: int


class PostgreSQL(BaseModel):
    image: Image
    enabled: bool
    postgresqlHost: str
    postgresqlUsername: str
    postgresqlPassword: str
    postgresqlDatabase: str
    service: Service
