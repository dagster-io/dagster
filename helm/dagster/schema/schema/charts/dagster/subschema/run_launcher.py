from enum import Enum
from typing import Any

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
    labels: kubernetes.Labels | None = None
    nodeSelector: kubernetes.NodeSelector | None = None
    configSource: dict | None = None
    additionalCeleryArgs: list[str] | None = None

    model_config = ConfigDict(extra="forbid")


class CeleryK8sRunLauncherConfig(BaseModel):
    image: kubernetes.Image
    imagePullPolicy: kubernetes.PullPolicy | None = None
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
    checkDbReadyInitContainer: bool | None = None
    livenessProbe: kubernetes.LivenessProbe
    volumeMounts: list[kubernetes.VolumeMount]
    volumes: list[kubernetes.Volume]
    labels: dict[str, str] | None = None
    failPodOnRunFailure: bool | None = None
    schedulerName: str | None = None
    jobNamespace: str | None = None

    model_config = ConfigDict(extra="forbid")


class RunK8sConfig(BaseModel):
    containerConfig: dict[str, Any] | None = None
    podSpecConfig: dict[str, Any] | None = None
    podTemplateSpecMetadata: dict[str, Any] | None = None
    jobSpecConfig: dict[str, Any] | None = None
    jobMetadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


class K8sRunLauncherConfig(BaseModel):
    image: kubernetes.Image | None = None
    imagePullPolicy: kubernetes.PullPolicy
    jobNamespace: str | None = None
    loadInclusterConfig: bool
    kubeconfigFile: str | None = None
    envConfigMaps: list[kubernetes.ConfigMapEnvSource]
    envSecrets: list[kubernetes.SecretEnvSource]
    envVars: list[str]
    volumeMounts: list[kubernetes.VolumeMount]
    volumes: list[kubernetes.Volume]
    labels: dict[str, str] | None = None
    failPodOnRunFailure: bool | None = None
    resources: kubernetes.ResourceRequirements | None = None
    schedulerName: str | None = None
    securityContext: kubernetes.SecurityContext | None = None
    runK8sConfig: RunK8sConfig | None = None

    model_config = ConfigDict(extra="forbid")


class RunLauncherConfig(BaseModel):
    celeryK8sRunLauncher: CeleryK8sRunLauncherConfig | None = None
    k8sRunLauncher: K8sRunLauncherConfig | None = None
    customRunLauncher: ConfigurableClass | None = None


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
