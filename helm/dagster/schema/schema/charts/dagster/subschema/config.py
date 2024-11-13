from typing import Union

from pydantic import BaseModel
from typing_extensions import TypeAlias


class Source(BaseModel, extra="forbid"):
    env: str


StringSource: TypeAlias = Union[str, Source]
IntSource: TypeAlias = Union[int, Source]
