from typing import Union

from pydantic import BaseModel, Extra  # pylint: disable=E0611


class _StringSource(BaseModel):
    env: str

    class Config:
        extra = Extra.forbid


StringSource = Union[str, _StringSource]
