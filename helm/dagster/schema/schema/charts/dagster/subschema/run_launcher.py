from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Extra, Field

from ...utils import kubernetes
from ...utils.utils import BaseModel, ConfigurableClass, create_json_schema_conditionals


class RunLauncherType(str, Enum):
    CELERY = "CeleryK8sRunLauncher"
    K8S = "K8sRunLauncher"
    CUSTOM = "CustomRunLauncher"


class CeleryWorkerQueue(BaseModel):
    replicaCount: int = Field(gt=0)
    name: str
    labels: Optional[kubernetes.Labels]
    nodeSelector: Optional[kubernetes.NodeSelector]
    configSource: Optional[dict]
    additionalCeleryArgs: Optional[List[str]]

    class Config:
        extra = Extra.forbid


class CeleryK8sRunLauncherConfig(BaseModel):
    image: kubernetes.Image
    imagePullPolicy: Optional[kubernetes.PullPolicy]
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
    volumeMounts: List[kubernetes.VolumeMount]
    volumes: List[kubernetes.Volume]
    labels: Optional[Dict[str, str]]
    failPodOnRunFailure: Optional[bool]
    schedulerName: Optional[str]
    jobNamespace: Optional[str]

    class Config:
        extra = Extra.forbid


class RunK8sConfig(BaseModel):
    containerConfig: Optional[Dict[str, Any]]
    podSpecConfig: Optional[Dict[str, Any]]
    podTemplateSpecMetadata: Optional[Dict[str, Any]]
    jobSpecConfig: Optional[Dict[str, Any]]
    jobMetadata: Optional[Dict[str, Any]]

    class Config:
        extra = Extra.forbid


class K8sRunLauncherConfig(BaseModel):
    image: Optional[kubernetes.Image]
    imagePullPolicy: kubernetes.PullPolicy
    jobNamespace: Optional[str]
    loadInclusterConfig: bool
    kubeconfigFile: Optional[str]
    envConfigMaps: List[kubernetes.ConfigMapEnvSource]
    envSecrets: List[kubernetes.SecretEnvSource]
    envVars: List[str]
    volumeMounts: List[kubernetes.VolumeMount]
    volumes: List[kubernetes.Volume]
    labels: Optional[Dict[str, str]]
    failPodOnRunFailure: Optional[bool]
    resources: Optional[kubernetes.ResourceRequirements]
    schedulerName: Optional[str]
    securityContext: Optional[kubernetes.SecurityContext]
    runK8sConfig: Optional[RunK8sConfig]

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
