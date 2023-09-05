from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import Extra

from ...utils import kubernetes
from ...utils.utils import BaseModel, ConfigurableClass, create_json_schema_conditionals
from .config import IntSource


class RunCoordinatorType(str, Enum):
    QUEUED = "QueuedRunCoordinator"
    CUSTOM = "CustomRunCoordinator"


class TagConcurrencyLimitConfig(BaseModel):
    applyLimitPerUniqueValue: bool

    class Config:
        extra = Extra.forbid


class TagConcurrencyLimit(BaseModel):
    value: Optional[Union[str, TagConcurrencyLimitConfig]] = None
    key: str
    limit: int

    class Config:
        extra = Extra.forbid


class QueuedRunCoordinatorConfig(BaseModel):
    maxConcurrentRuns: Optional[IntSource] = None
    tagConcurrencyLimits: Optional[List[TagConcurrencyLimit]] = None
    dequeueIntervalSeconds: Optional[IntSource] = None
    dequeueNumWorkers: Optional[IntSource] = None
    dequeueUseThreads: Optional[bool] = None

    class Config:
        extra = Extra.forbid


class RunCoordinatorConfig(BaseModel):
    queuedRunCoordinator: Optional[QueuedRunCoordinatorConfig] = None
    customRunCoordinator: Optional[ConfigurableClass] = None


class RunCoordinator(BaseModel):
    enabled: bool
    type: RunCoordinatorType
    config: RunCoordinatorConfig

    class Config:
        extra = Extra.forbid
        schema_extra = {
            "allOf": create_json_schema_conditionals(
                {
                    RunCoordinatorType.QUEUED: "queuedRunCoordinator",
                    RunCoordinatorType.CUSTOM: "customRunCoordinator",
                }
            )
        }


class Sensors(BaseModel):
    numWorkers: Optional[int] = None
    numSubmitWorkers: Optional[int] = None
    useThreads: bool


class Schedules(BaseModel):
    numWorkers: Optional[int] = None
    numSubmitWorkers: Optional[int] = None
    useThreads: bool


class Daemon(BaseModel):
    schedulerName: Optional[str] = None
    volumeMounts: Optional[List[kubernetes.VolumeMount]] = None
    volumes: Optional[List[kubernetes.Volume]] = None
    enabled: bool
    image: kubernetes.Image
    runCoordinator: RunCoordinator
    heartbeatTolerance: int
    env: Union[Dict[str, str], List[kubernetes.EnvVar]]
    envConfigMaps: List[kubernetes.ConfigMapEnvSource]
    envSecrets: List[kubernetes.SecretEnvSource]
    deploymentLabels: Dict[str, str]
    labels: Dict[str, str]
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
    runMonitoring: Dict[str, Any]
    runRetries: Dict[str, Any]
    sensors: Sensors
    schedules: Schedules

    class Config:
        extra = Extra.forbid
