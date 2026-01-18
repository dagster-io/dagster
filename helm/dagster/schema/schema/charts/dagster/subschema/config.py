from typing import TypeAlias, Union

from pydantic import BaseModel


class Source(BaseModel, extra="forbid"):
    env: str


StringSource: TypeAlias = Union[str, Source]
IntSource: TypeAlias = Union[int, Source]
