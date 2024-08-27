from pydantic import BaseModel

from schema.charts.utils.kubernetes import ExternalImage


class Busybox(BaseModel):
    image: ExternalImage
