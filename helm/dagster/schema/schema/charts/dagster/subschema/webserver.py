from schema.charts.utils import kubernetes
from schema.charts.utils.utils import BaseModel


class Server(BaseModel):
    host: str
    port: int
    name: str | None = None
    ssl: bool | None = None


class Workspace(BaseModel):
    enabled: bool
    servers: list[Server]
    externalConfigmap: str | None = None


class Webserver(BaseModel, extra="forbid"):
    replicaCount: int
    image: kubernetes.Image
    nameOverride: str
    pathPrefix: str | None = None
    service: kubernetes.Service
    workspace: Workspace
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
    checkDbReadyInitContainer: bool | None = None
    resources: kubernetes.Resources
    readinessProbe: kubernetes.ReadinessProbe
    livenessProbe: kubernetes.LivenessProbe
    startupProbe: kubernetes.StartupProbe
    annotations: kubernetes.Annotations
    enableReadOnly: bool
    dbStatementTimeout: int | None = None
    dbPoolRecycle: int | None = None
    dbPoolMaxOverflow: int | None = None
    logLevel: str | None = None
    logFormat: str | None = None
    schedulerName: str | None = None
    volumeMounts: list[kubernetes.VolumeMount] | None = None
    volumes: list[kubernetes.Volume] | None = None
    initContainerResources: kubernetes.Resources | None = None
    extraContainers: list[kubernetes.Container] | None = None
    extraPrependedInitContainers: list[kubernetes.InitContainer] | None = None
