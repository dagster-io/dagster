from typing import Annotated

from pydantic import BaseModel, Field, GetJsonSchemaHandler, create_model
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema

from schema.charts.utils import kubernetes


class _RequireName:
    """Annotation that overlays ``required: ["name"]`` onto a ``UserDeployment``'s JSON
    schema. Applied only to the list form of ``deployments`` so that a missing ``name`` in
    an array entry is still caught by schema validation (``helm lint``), while the map form
    — where the map key supplies the name — leaves ``name`` optional. Reuses the shared
    ``UserDeployment`` ``$def`` via ``allOf`` rather than duplicating it.
    """

    def __get_pydantic_json_schema__(
        self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"allOf": [handler(core_schema), {"required": ["name"]}]}


class UserDeploymentIncludeConfigInLaunchedRuns(BaseModel):
    enabled: bool


ReadinessProbeWithEnabled = create_model(
    "ReadinessProbeWithEnabled", __base__=(kubernetes.ReadinessProbe), enabled=(bool, ...)
)


class UserDeployment(BaseModel):
    # Optional so that deployments can be supplied as a name-keyed map, where the
    # map key provides the name. For the list form, the Helm templates require a name.
    name: str | None = None
    image: kubernetes.Image
    dagsterApiGrpcArgs: list[str] | None = None
    codeServerArgs: list[str] | None = None
    includeConfigInLaunchedRuns: UserDeploymentIncludeConfigInLaunchedRuns | None = None
    deploymentNamespace: str | None = None
    port: int
    replicaCount: int = Field(default=1, gt=0)
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


# `deployments` may be either a list of deployments (each requiring a `name`) or a map
# keyed by deployment name (where the key supplies the name, so `name` is optional).
UserDeploymentsValue = list[Annotated[UserDeployment, _RequireName()]] | dict[str, UserDeployment]


class UserDeployments(BaseModel):
    enabled: bool
    enableSubchart: bool
    imagePullSecrets: list[kubernetes.SecretRef]
    deployments: UserDeploymentsValue
