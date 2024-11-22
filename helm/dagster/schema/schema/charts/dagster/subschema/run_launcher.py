from enum import Enum
from typing import Any, Optional

from pydantic import ConfigDict, Field

from schema.charts.utils import kubernetes
from schema.charts.utils.utils import BaseModel, ConfigurableClass, create_json_schema_conditionals


class RunLauncherType(str, Enum):
    CELERY = "CeleryK8sRunLauncher"
    K8S = "K8sRunLauncher"
    CUSTOM = "CustomRunLauncher"


class CeleryWorkerQueue(BaseModel):
    replicaCount: int = Field(gt=0)
    name: str
    labels: Optional[kubernetes.Labels] = None
    nodeSelector: Optional[kubernetes.NodeSelector] = None
    configSource: Optional[dict] = None
    additionalCeleryArgs: Optional[list[str]] = None

    model_config = ConfigDict(extra="forbid")


class CeleryK8sRunLauncherConfig(BaseModel):
    image: kubernetes.Image
    imagePullPolicy: Optional[kubernetes.PullPolicy] = None
    nameOverride: str
    configSource: dict
    workerQueues: list[CeleryWorkerQueue] = Field(min_items=1)
    env: dict[str, str]
    envConfigMaps: list[kubernetes.ConfigMapEnvSource]
    envSecrets: list[kubernetes.SecretEnvSource]
    annotations: kubernetes.Annotations
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    resources: kubernetes.Resources
    livenessProbe: kubernetes.LivenessProbe
    volumeMounts: list[kubernetes.VolumeMount]
    volumes: list[kubernetes.Volume]
    labels: Optional[dict[str, str]] = None
    failPodOnRunFailure: Optional[bool] = None
    schedulerName: Optional[str] = None
    jobNamespace: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class RunK8sConfig(BaseModel):
    containerConfig: Optional[dict[str, Any]] = None
    podSpecConfig: Optional[dict[str, Any]] = None
    podTemplateSpecMetadata: Optional[dict[str, Any]] = None
    jobSpecConfig: Optional[dict[str, Any]] = None
    jobMetadata: Optional[dict[str, Any]] = None

    model_config = ConfigDict(extra="forbid")


class K8sRunLauncherConfig(BaseModel):
    image: Optional[kubernetes.Image] = None
    imagePullPolicy: kubernetes.PullPolicy
    jobNamespace: Optional[str] = None
    loadInclusterConfig: bool
    kubeconfigFile: Optional[str] = None
    envConfigMaps: list[kubernetes.ConfigMapEnvSource]
    envSecrets: list[kubernetes.SecretEnvSource]
    envVars: list[str]
    volumeMounts: list[kubernetes.VolumeMount]
    volumes: list[kubernetes.Volume]
    labels: Optional[dict[str, str]] = None
    failPodOnRunFailure: Optional[bool] = None
    resources: Optional[kubernetes.ResourceRequirements] = None
    schedulerName: Optional[str] = None
    securityContext: Optional[kubernetes.SecurityContext] = None
    runK8sConfig: Optional[RunK8sConfig] = None

    model_config = ConfigDict(extra="forbid")


class RunLauncherConfig(BaseModel):
    celeryK8sRunLauncher: Optional[CeleryK8sRunLauncherConfig] = None
    k8sRunLauncher: Optional[K8sRunLauncherConfig] = None
    customRunLauncher: Optional[ConfigurableClass] = None


class RunLauncher(BaseModel):
    type: RunLauncherType
    config: RunLauncherConfig

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "allOf": create_json_schema_conditionals(
                {
                    RunLauncherType.CELERY: "celeryK8sRunLauncher",
                    RunLauncherType.K8S: "k8sRunLauncher",
                    RunLauncherType.CUSTOM: "customRunLauncher",
                }
            )
        },
    )
