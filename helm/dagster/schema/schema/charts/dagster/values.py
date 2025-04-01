from collections.abc import Mapping
from typing import Any, Optional

from pydantic import BaseModel, Field

from schema.charts.dagster import subschema
from schema.charts.dagster_user_deployments.subschema.user_deployments import UserDeployments
from schema.charts.utils import kubernetes


# We have `extra="allow"` here to support passing `dagit` as an alias for `dagsterWebserver` when
# constructing without validation. This can be removed in 2.0 since we will no longer support the
# dagit alias. It is possible there is a better way to do this using Pydantic field aliases, but the
# current solution does work.
class DagsterHelmValues(BaseModel, extra="allow"):
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
    imagePullSecrets: list[kubernetes.SecretRef]
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
    additionalInstanceConfig: Optional[Mapping[str, Any]] = None
