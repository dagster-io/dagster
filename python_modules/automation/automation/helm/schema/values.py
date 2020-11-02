from pydantic import BaseModel  # pylint: disable=E0611

from .dagit import Dagit
from .postgresql import PostgreSQL
from .rabbitmq import RabbitMQ


class HelmValues(BaseModel):
    """
    Schema for Helm values.
    """

    dagit: Dagit
    postgresql: PostgreSQL
    rabbitmq: RabbitMQ
