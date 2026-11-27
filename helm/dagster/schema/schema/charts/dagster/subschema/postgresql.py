from pydantic import BaseModel

from schema.charts.utils.kubernetes import ExternalImage


class Service(BaseModel):
    port: int


class Pool(BaseModel):
    size: int | None = None
    maxOverflow: int | None = None
    recycle: int | None = None
    mode: str | None = None


class PostgreSQL(BaseModel):
    image: ExternalImage
    enabled: bool
    postgresqlHost: str
    postgresqlUsername: str
    postgresqlPassword: str
    postgresqlDatabase: str
    postgresqlParams: dict
    postgresqlScheme: str | None = None
    service: Service
    pool: Pool | None = None
