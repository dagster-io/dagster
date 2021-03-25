from pydantic import BaseModel  # pylint: disable=no-name-in-module


class ServiceAccount(BaseModel):
    create: bool
    name: str
