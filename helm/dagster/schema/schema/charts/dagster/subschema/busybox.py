from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils.kubernetes import Image


class Busybox(BaseModel):
    image: Image
