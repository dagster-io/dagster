from pydantic import BaseModel, Field  # pylint: disable=E0611


class RabbitMQConfiguration(BaseModel):
    username: str
    password: str


class Service(BaseModel):
    port: int


class VolumePermissions(BaseModel):
    enabled: bool = Field(default=True, const=True)


class RabbitMQ(BaseModel):
    enabled: bool
    rabbitmq: RabbitMQConfiguration
    service: Service
    volumePermissions: VolumePermissions
