from pydantic import BaseModel  # pylint: disable=no-name-in-module


class Migrate(BaseModel):
    enabled: bool
