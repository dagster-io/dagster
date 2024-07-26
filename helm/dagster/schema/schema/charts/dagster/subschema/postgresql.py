from typing import Optional

from pydantic import BaseModel

from schema.charts.utils.kubernetes import ExternalImage


class Service(BaseModel):
    port: int


class PostgreSQL(BaseModel):
    image: ExternalImage
    enabled: bool
    pgIsReadyCommandOverride: Optional[str]
    postgresqlHost: str
    postgresqlUsername: str
    postgresqlPassword: str
    postgresqlDatabase: str
    postgresqlParams: dict
    postgresqlScheme: Optional[str]
    service: Service
