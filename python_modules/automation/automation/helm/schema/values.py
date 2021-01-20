from typing import List

from pydantic import BaseModel  # pylint: disable=E0611

from . import subschema


class HelmValues(BaseModel):
    """
    Schema for Helm values.
    """

    dagit: subschema.Dagit
    userDeployments: subschema.UserDeployments
    postgresql: subschema.PostgreSQL
    rabbitmq: subschema.RabbitMQ
    redis: subschema.Redis
    flower: subschema.Flower
    ingress: subschema.Ingress
    imagePullSecrets: List[subschema.kubernetes.SecretRef]
    computeLogManager: subschema.ComputeLogManager
    scheduler: subschema.Scheduler
    runLauncher: subschema.RunLauncher
    dagsterDaemon: subschema.Daemon
