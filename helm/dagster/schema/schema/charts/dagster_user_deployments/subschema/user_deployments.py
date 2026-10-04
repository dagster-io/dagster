from typing import Optional, Union

from pydantic import BaseModel, Field, create_model, field_validator

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


class UserDeploymentDictEntry(UserDeployment):
    """The shape of a value in the dict form of `deployments`.

    Identical to UserDeployment, except `name` comes from the dict key rather than the
    value itself, so it must not be required here. This is kept as its own model (instead
    of reusing UserDeployment in the `dict[str, ...]` arm of the `deployments` Union) so it
    gets its own entry in the generated JSON schema: the array form can still require
    `name` in `values.schema.json` without that requirement leaking into the dict form.
    """

    name: Optional[str] = None


def normalize_deployments(
    v: Union[list[UserDeployment], dict[str, "UserDeploymentDictEntry | dict"]],
) -> Union[list[UserDeployment], dict]:
    """Convert `deployments` from dict format to list format.

    If `deployments` is provided as a dictionary with deployment names as keys, this
    converts it to a list of UserDeployment objects, ensuring the 'name' field of each
    deployment is set to its dictionary key (overriding any `name` given in the value
    itself). List input is returned unchanged.

    Shared between `UserDeployments.deployments` (the `dagster-user-deployments` section
    of the umbrella `dagster` chart) and `DagsterUserDeploymentsHelmValues.deployments`
    (the standalone `dagster-user-deployments` subchart) so both entry points accept and
    normalize the dict format identically.
    """
    if not isinstance(v, dict):
        return v

    deployments_list: list[UserDeployment] = []
    for key, deployment_data in v.items():
        if isinstance(deployment_data, UserDeployment):
            deployment_dict = deployment_data.model_dump()
        elif isinstance(deployment_data, dict):
            deployment_dict = deployment_data.copy()
        else:
            deployment_dict = dict(deployment_data)

        # ALWAYS set name to the dictionary key
        deployment_dict["name"] = key

        deployments_list.append(UserDeployment(**deployment_dict))

    return deployments_list


class UserDeployments(BaseModel):
    enabled: bool
    enableSubchart: bool
    imagePullSecrets: list[kubernetes.SecretRef]
    deployments: Union[list[UserDeployment], dict[str, UserDeploymentDictEntry]]

    @field_validator("deployments", mode="before")
    @classmethod
    def convert_deployments_dict_to_list(
        cls, v: Union[list[UserDeployment], dict[str, UserDeploymentDictEntry]]
    ) -> list[UserDeployment]:
        return normalize_deployments(v)
