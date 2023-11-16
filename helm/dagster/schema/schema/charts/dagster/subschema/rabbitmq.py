from pydantic import BaseModel
from typing_extensions import Literal

from ...utils.kubernetes import ExternalImage


class RabbitMQConfiguration(BaseModel):
    username: str
    password: str


class Service(BaseModel):
    port: int


class VolumePermissions(BaseModel):
    enabled: Literal[True] = True
    image: ExternalImage


class RabbitMQ(BaseModel):
    enabled: bool
    image: ExternalImage
    rabbitmq: RabbitMQConfiguration
    service: Service
    volumePermissions: VolumePermissions
