from pydantic import BaseModel

from ...utils.kubernetes import ExternalImage


class Busybox(BaseModel):
    image: ExternalImage
