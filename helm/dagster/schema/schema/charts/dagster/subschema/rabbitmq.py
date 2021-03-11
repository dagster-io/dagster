from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from ...utils.kubernetes import ImageWithRegistry


class RabbitMQConfiguration(BaseModel):
    username: str
    password: str


class Service(BaseModel):
    port: int


class VolumePermissions(BaseModel):
    enabled: bool = Field(default=True, const=True)
    image: ImageWithRegistry


class RabbitMQ(BaseModel):
    enabled: bool
    image: ImageWithRegistry
    rabbitmq: RabbitMQConfiguration
    service: Service
    volumePermissions: VolumePermissions
