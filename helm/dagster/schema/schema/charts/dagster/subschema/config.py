from typing import Union

from pydantic import BaseModel, Extra  # pylint: disable=no-name-in-module


class Source(BaseModel):
    env: str

    class Config:
        extra = Extra.forbid


StringSource = Union[str, Source]
IntSource = Union[int, Source]
