from pydantic import BaseModel


class Migrate(BaseModel):
    enabled: bool
