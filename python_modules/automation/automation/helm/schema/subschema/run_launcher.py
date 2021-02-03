from enum import Enum
from typing import Dict, List, Optional

from pydantic import Extra, Field  # pylint: disable=E0611

from . import kubernetes
from .utils import BaseModel, ConfigurableClass, create_json_schema_conditionals


class RunLauncherType(str, Enum):
    CELERY = "CeleryK8sRunLauncher"
    K8S = "K8sRunLauncher"
    CUSTOM = "CustomRunLauncher"


class CeleryWorkerQueue(BaseModel):
    replicaCount: int = Field(gt=0)
    name: str
    labels: Optional[kubernetes.Labels]

    class Config:
        extra = Extra.forbid


class CeleryK8sRunLauncherConfig(BaseModel):
    image: kubernetes.Image
    nameOverride: str
    configSource: dict
    workerQueues: List[CeleryWorkerQueue] = Field(min_items=1)
    env: Dict[str, str]
    envConfigMaps: List[kubernetes.ConfigMapEnvSource]
    envSecrets: List[kubernetes.SecretEnvSource]
    annotations: kubernetes.Annotations
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    resources: kubernetes.Resources
    livenessProbe: kubernetes.LivenessProbe

    class Config:
        extra = Extra.forbid


class K8sRunLauncherConfig(BaseModel):
    image: Optional[kubernetes.Image]
    jobNamespace: Optional[str]
    loadInclusterConfig: bool
    kubeconfigFile: Optional[str]
    envConfigMaps: List[kubernetes.ConfigMapEnvSource]
    envSecrets: List[kubernetes.SecretEnvSource]

    class Config:
        extra = Extra.forbid


class RunLauncherConfig(BaseModel):
    celeryK8sRunLauncher: Optional[CeleryK8sRunLauncherConfig]
    k8sRunLauncher: Optional[K8sRunLauncherConfig]
    customRunLauncher: Optional[ConfigurableClass]


class RunLauncher(BaseModel):
    type: RunLauncherType
    config: RunLauncherConfig

    class Config:
        extra = Extra.forbid
        schema_extra = {
            "allOf": create_json_schema_conditionals(
                {
                    RunLauncherType.CELERY: "celeryK8sRunLauncher",
                    RunLauncherType.K8S: "k8sRunLauncher",
                    RunLauncherType.CUSTOM: "customRunLauncher",
                }
            )
        }
