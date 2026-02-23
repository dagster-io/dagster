from enum import Enum
from typing import Any

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
    value: str | TagConcurrencyLimitConfig | None = None
    limit: int


class BlockOpConcurrencyLimitedRuns(BaseModel):
    enabled: bool
    opConcurrencySlotBuffer: int


class QueuedRunCoordinatorConfig(BaseModel, extra="forbid"):
    maxConcurrentRuns: IntSource | None = None
    tagConcurrencyLimits: list[TagConcurrencyLimit] | None = None
    dequeueIntervalSeconds: IntSource | None = None
    dequeueNumWorkers: IntSource | None = None
    dequeueUseThreads: bool | None = None
    blockOpConcurrencyLimitedRuns: BlockOpConcurrencyLimitedRuns | None = None


class RunCoordinatorConfig(BaseModel):
    queuedRunCoordinator: QueuedRunCoordinatorConfig | None = None
    customRunCoordinator: ConfigurableClass | None = None


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
    numWorkers: int | None = None
    numSubmitWorkers: int | None = None


class Schedules(BaseModel):
    useThreads: bool
    numWorkers: int | None = None
    numSubmitWorkers: int | None = None


class Backfills(BaseModel):
    useThreads: bool
    numWorkers: int | None = None
    numSubmitWorkers: int | None = None


class RunRetries(BaseModel):
    enabled: bool
    maxRetries: int | None = None
    retryOnAssetOrOpFailure: bool | None = None


class Daemon(BaseModel, extra="forbid"):
    enabled: bool
    image: kubernetes.Image
    runCoordinator: RunCoordinator
    heartbeatTolerance: int
    env: dict[str, str] | list[kubernetes.EnvVar]
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
    checkDbReadyInitContainer: bool | None = None
    livenessProbe: kubernetes.LivenessProbe
    readinessProbe: kubernetes.ReadinessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: kubernetes.Annotations
    runMonitoring: dict[str, Any]
    runRetries: RunRetries
    sensors: Sensors
    schedules: Schedules
    backfills: Backfills | None = None
    schedulerName: str | None = None
    logFormat: str | None = None
    volumeMounts: list[kubernetes.VolumeMount] | None = None
    volumes: list[kubernetes.Volume] | None = None
    initContainerResources: kubernetes.Resources | None = None
    extraContainers: list[kubernetes.Container] | None = None
    extraPrependedInitContainers: list[kubernetes.InitContainer] | None = None
