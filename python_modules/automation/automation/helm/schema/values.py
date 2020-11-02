from pydantic import BaseModel  # pylint: disable=E0611

from . import subschema


class HelmValues(BaseModel):
    """
    Schema for Helm values.
    """

    dagit: subschema.Dagit
    postgresql: subschema.PostgreSQL
    rabbitmq: subschema.RabbitMQ
    redis: subschema.Redis
    flower: subschema.Flower
    ingress: subschema.Ingress
