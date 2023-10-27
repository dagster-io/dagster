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
    key: str
    value: Optional[Union[str, TagConcurrencyLimitConfig]]
    limit: int

    class Config:
        extra = Extra.forbid


class QueuedRunCoordinatorConfig(BaseModel):
    maxConcurrentRuns: Optional[IntSource]
    tagConcurrencyLimits: Optional[List[TagConcurrencyLimit]]
    dequeueIntervalSeconds: Optional[IntSource]
    dequeueNumWorkers: Optional[IntSource]
    dequeueUseThreads: Optional[bool]

    class Config:
        extra = Extra.forbid


class RunCoordinatorConfig(BaseModel):
    queuedRunCoordinator: Optional[QueuedRunCoordinatorConfig]
    customRunCoordinator: Optional[ConfigurableClass]


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
    useThreads: bool
    numWorkers: Optional[int]
    numSubmitWorkers: Optional[int]


class Schedules(BaseModel):
    useThreads: bool
    numWorkers: Optional[int]
    numSubmitWorkers: Optional[int]


class Daemon(BaseModel):
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
    schedulerName: Optional[str]
    volumeMounts: Optional[List[kubernetes.VolumeMount]]
    volumes: Optional[List[kubernetes.Volume]]

    class Config:
        extra = Extra.forbid
