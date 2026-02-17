from typing import TypeAlias

from pydantic import BaseModel


class Source(BaseModel, extra="forbid"):
    env: str


StringSource: TypeAlias = str | Source
IntSource: TypeAlias = int | Source
