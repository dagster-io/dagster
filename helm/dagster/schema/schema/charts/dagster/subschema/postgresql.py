from typing import Optional

from pydantic import BaseModel

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
    postgresqlScheme: Optional[str]
    service: Service
