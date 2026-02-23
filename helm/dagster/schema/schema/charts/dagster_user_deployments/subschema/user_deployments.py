from pydantic import BaseModel, create_model

from schema.charts.utils import kubernetes


class UserDeploymentIncludeConfigInLaunchedRuns(BaseModel):
    enabled: bool


ReadinessProbeWithEnabled = create_model(
    "ReadinessProbeWithEnabled", __base__=(kubernetes.ReadinessProbe), enabled=(bool, ...)
)


class UserDeployment(BaseModel):
    name: str
    image: kubernetes.Image
    dagsterApiGrpcArgs: list[str] | None = None
    codeServerArgs: list[str] | None = None
    includeConfigInLaunchedRuns: UserDeploymentIncludeConfigInLaunchedRuns | None = None
    deploymentNamespace: str | None = None
    port: int
    env: dict[str, str] | list[kubernetes.EnvVar] | None = None
    envConfigMaps: list[kubernetes.ConfigMapEnvSource] | None = None
    envSecrets: list[kubernetes.SecretEnvSource] | None = None
    annotations: kubernetes.Annotations | None = None
    nodeSelector: kubernetes.NodeSelector | None = None
    affinity: kubernetes.Affinity | None = None
    tolerations: kubernetes.Tolerations | None = None
    podSecurityContext: kubernetes.PodSecurityContext | None = None
    securityContext: kubernetes.SecurityContext | None = None
    resources: kubernetes.Resources | None = None
    livenessProbe: kubernetes.LivenessProbe | None = None
    readinessProbe: ReadinessProbeWithEnabled | None = None
    startupProbe: kubernetes.StartupProbe | None = None
    labels: dict[str, str] | None = None
    volumeMounts: list[kubernetes.VolumeMount] | None = None
    volumes: list[kubernetes.Volume] | None = None
    schedulerName: str | None = None
    initContainers: (
        list[kubernetes.Container | kubernetes.InitContainerWithStructuredImage] | None
    ) = None
    sidecarContainers: list[kubernetes.Container] | None = None
    deploymentStrategy: kubernetes.DeploymentStrategy | None = None


class UserDeployments(BaseModel):
    enabled: bool
    enableSubchart: bool
    imagePullSecrets: list[kubernetes.SecretRef]
    deployments: list[UserDeployment]
