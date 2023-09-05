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
    labels: Optional[kubernetes.Labels] = None
    nodeSelector: Optional[kubernetes.NodeSelector] = None
    configSource: Optional[dict] = None
    additionalCeleryArgs: Optional[List[str]] = None
    replicaCount: int = Field(gt=0)
    name: str

    class Config:
        extra = Extra.forbid


class CeleryK8sRunLauncherConfig(BaseModel):
    labels: Optional[Dict[str, str]] = None
    failPodOnRunFailure: Optional[bool] = None
    schedulerName: Optional[str] = None
    jobNamespace: Optional[str] = None
    imagePullPolicy: Optional[kubernetes.PullPolicy] = None
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
    volumeMounts: List[kubernetes.VolumeMount]
    volumes: List[kubernetes.Volume]

    class Config:
        extra = Extra.forbid


class RunK8sConfig(BaseModel):
    containerConfig: Optional[Dict[str, Any]] = None
    podSpecConfig: Optional[Dict[str, Any]] = None
    podTemplateSpecMetadata: Optional[Dict[str, Any]] = None
    jobSpecConfig: Optional[Dict[str, Any]] = None
    jobMetadata: Optional[Dict[str, Any]] = None

    class Config:
        extra = Extra.forbid


class K8sRunLauncherConfig(BaseModel):
    image: Optional[kubernetes.Image] = None
    labels: Optional[Dict[str, str]] = None
    failPodOnRunFailure: Optional[bool] = None
    resources: Optional[kubernetes.ResourceRequirements] = None
    schedulerName: Optional[str] = None
    securityContext: Optional[kubernetes.SecurityContext] = None
    runK8sConfig: Optional[RunK8sConfig] = None
    jobNamespace: Optional[str] = None
    kubeconfigFile: Optional[str] = None
    imagePullPolicy: kubernetes.PullPolicy
    loadInclusterConfig: bool
    envConfigMaps: List[kubernetes.ConfigMapEnvSource]
    envSecrets: List[kubernetes.SecretEnvSource]
    envVars: List[str]
    volumeMounts: List[kubernetes.VolumeMount]
    volumes: List[kubernetes.Volume]

    class Config:
        extra = Extra.forbid


class RunLauncherConfig(BaseModel):
    celeryK8sRunLauncher: Optional[CeleryK8sRunLauncherConfig] = None
    k8sRunLauncher: Optional[K8sRunLauncherConfig] = None
    customRunLauncher: Optional[ConfigurableClass] = None


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
