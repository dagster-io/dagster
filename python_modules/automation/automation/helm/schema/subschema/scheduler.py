from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Extra  # pylint: disable=E0611

from . import kubernetes
from .utils import BaseModel, create_json_schema_conditionals


class SchedulerType(str, Enum):
    DAEMON = "DagsterDaemonScheduler"
    K8S = "K8sScheduler"


class K8sSchedulerConfig(BaseModel):
    image: kubernetes.Image
    schedulerNamespace: Optional[str]
    loadInclusterConfig: bool
    kubeconfigFile: Optional[str]
    envSecrets: List[kubernetes.SecretEnvSource]

    class Config:
        extra = Extra.forbid


class SchedulerConfig(BaseModel):
    k8sScheduler: Optional[K8sSchedulerConfig]

    class Config:
        extra = Extra.forbid


class Scheduler(BaseModel):
    type: SchedulerType
    config: SchedulerConfig

    class Config:
        extra = Extra.forbid
        schema_extra = {
            "allOf": create_json_schema_conditionals({SchedulerType.K8S: "k8sScheduler"})
        }
