from pydantic import BaseModel  # pylint: disable=no-name-in-module

from ...utils.kubernetes import ExternalImage


class Busybox(BaseModel):
    image: ExternalImage
