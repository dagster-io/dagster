from typing import Any, List, Mapping, Optional

from pydantic import BaseModel, Field

from ..dagster_user_deployments.subschema.user_deployments import UserDeployments
from ..utils import kubernetes
from . import subschema


class DagsterHelmValues(BaseModel):
    __doc__ = "@" + "generated"

    dagsterWebserver: subschema.Webserver
    dagsterUserDeployments: UserDeployments = Field(..., alias="dagster-user-deployments")
    postgresql: subschema.PostgreSQL
    generatePostgresqlPasswordSecret: bool
    generateCeleryConfigSecret: bool
    rabbitmq: subschema.RabbitMQ
    redis: subschema.Redis
    flower: subschema.Flower
    ingress: subschema.Ingress
    imagePullSecrets: List[kubernetes.SecretRef]
    computeLogManager: subschema.ComputeLogManager
    scheduler: subschema.Scheduler
    runLauncher: subschema.RunLauncher
    pythonLogs: subschema.PythonLogs
    dagsterDaemon: subschema.Daemon
    busybox: subschema.Busybox
    migrate: subschema.Migrate
    telemetry: subschema.Telemetry
    serviceAccount: subschema.ServiceAccount
    global_: subschema.Global = Field(..., alias="global")
    retention: subschema.Retention
    additionalInstanceConfig: Optional[Mapping[str, Any]]
