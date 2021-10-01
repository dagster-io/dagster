from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import Extra  # pylint: disable=no-name-in-module

from ...utils import kubernetes
from ...utils.utils import BaseModel, ConfigurableClass, create_json_schema_conditionals
from .config import IntSource


class RunCoordinatorType(str, Enum):
    QUEUED = "QueuedRunCoordinator"
    CUSTOM = "CustomRunCoordinator"


class TagConcurrencyLimit(BaseModel):
    key: str
    value: Optional[Union[Dict, str]]
    limit: int

    class Config:
        extra = Extra.forbid


class QueuedRunCoordinatorConfig(BaseModel):
    maxConcurrentRuns: Optional[IntSource]
    tagConcurrencyLimits: Optional[List[TagConcurrencyLimit]]
    dequeueIntervalSeconds: Optional[IntSource]

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


class Daemon(BaseModel):
    enabled: bool
    image: kubernetes.Image
    runCoordinator: RunCoordinator
    heartbeatTolerance: int
    env: Dict[str, str]
    envConfigMaps: List[kubernetes.ConfigMapEnvSource]
    envSecrets: List[kubernetes.SecretEnvSource]
    nodeSelector: kubernetes.NodeSelector
    affinity: kubernetes.Affinity
    tolerations: kubernetes.Tolerations
    podSecurityContext: kubernetes.PodSecurityContext
    securityContext: kubernetes.SecurityContext
    resources: kubernetes.Resources
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: kubernetes.Annotations
