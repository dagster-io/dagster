from enum import Enum
from typing import Any, Optional, Union

from pydantic import ConfigDict

from schema.charts.dagster.subschema.config import IntSource
from schema.charts.utils import kubernetes
from schema.charts.utils.utils import BaseModel, ConfigurableClass, create_json_schema_conditionals


class RunCoordinatorType(str, Enum):
    QUEUED = "QueuedRunCoordinator"
    CUSTOM = "CustomRunCoordinator"


class TagConcurrencyLimitConfig(BaseModel, extra="forbid"):
    applyLimitPerUniqueValue: bool


class TagConcurrencyLimit(BaseModel, extra="forbid"):
    key: str
    value: Optional[Union[str, TagConcurrencyLimitConfig]] = None
    limit: int


class BlockOpConcurrencyLimitedRuns(BaseModel):
    enabled: bool
    opConcurrencySlotBuffer: int


class QueuedRunCoordinatorConfig(BaseModel, extra="forbid"):
    maxConcurrentRuns: Optional[IntSource] = None
    tagConcurrencyLimits: Optional[list[TagConcurrencyLimit]] = None
    dequeueIntervalSeconds: Optional[IntSource] = None
    dequeueNumWorkers: Optional[IntSource] = None
    dequeueUseThreads: Optional[bool] = None
    blockOpConcurrencyLimitedRuns: Optional[BlockOpConcurrencyLimitedRuns] = None


class RunCoordinatorConfig(BaseModel):
    queuedRunCoordinator: Optional[QueuedRunCoordinatorConfig] = None
    customRunCoordinator: Optional[ConfigurableClass] = None


class RunCoordinator(BaseModel):
    enabled: bool
    type: RunCoordinatorType
    config: RunCoordinatorConfig

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "allOf": create_json_schema_conditionals(
                {
                    RunCoordinatorType.QUEUED: "queuedRunCoordinator",
                    RunCoordinatorType.CUSTOM: "customRunCoordinator",
                }
            )
        },
    )


class Sensors(BaseModel):
    useThreads: bool
    numWorkers: Optional[int] = None
    numSubmitWorkers: Optional[int] = None


class Schedules(BaseModel):
    useThreads: bool
    numWorkers: Optional[int] = None
    numSubmitWorkers: Optional[int] = None


class RunRetries(BaseModel):
    enabled: bool
    maxRetries: Optional[int] = None
    retryOnAssetOrOpFailure: Optional[bool] = None


class Daemon(BaseModel, extra="forbid"):
    enabled: bool
    image: kubernetes.Image
    runCoordinator: RunCoordinator
    heartbeatTolerance: int
    env: Union[dict[str, str], list[kubernetes.EnvVar]]
    envConfigMaps: list[kubernetes.ConfigMapEnvSource]
    envSecrets: list[kubernetes.SecretEnvSource]
    deploymentLabels: dict[str, str]
    labels: dict[str, str]
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    resources: kubernetes.Resources
    livenessProbe: kubernetes.LivenessProbe
    readinessProbe: kubernetes.ReadinessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: kubernetes.Annotations
    runMonitoring: dict[str, Any]
    runRetries: RunRetries
    sensors: Sensors
    schedules: Schedules
    schedulerName: Optional[str] = None
    volumeMounts: Optional[list[kubernetes.VolumeMount]] = None
    volumes: Optional[list[kubernetes.Volume]] = None
    initContainerResources: Optional[kubernetes.Resources] = None
