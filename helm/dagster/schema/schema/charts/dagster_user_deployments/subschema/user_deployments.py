from typing import Union

from pydantic import BaseModel, create_model, field_validator

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
    deployments: Union[list[UserDeployment], dict[str, UserDeployment]]

    @field_validator("deployments", mode="before")
    @classmethod
    def convert_deployments_dict_to_list(
        cls, v: Union[list[UserDeployment], dict[str, UserDeployment]]
    ) -> list[UserDeployment]:
        """Convert deployments from dict format to list format.

        If deployments is provided as a dictionary with deployment names as keys,
        this validator converts it to a list of UserDeployment objects, ensuring
        the 'name' field of each deployment is set to its dictionary key.

        Args:
            v: Deployments as either a list or dict

        Returns:
            List of UserDeployment objects with names set from dict keys
        """
        if isinstance(v, dict):
            deployments_list: list[UserDeployment] = []
            for key, deployment_data in v.items():
                # Ensure we have a dictionary to work with
                if isinstance(deployment_data, UserDeployment):
                    deployment_dict = deployment_data.model_dump()
                elif isinstance(deployment_data, dict):
                    deployment_dict = deployment_data.copy()
                else:
                    deployment_dict = dict(deployment_data)

                # ALWAYS set name to the dictionary key
                deployment_dict["name"] = key

                # Create UserDeployment with the corrected name
                deployments_list.append(UserDeployment(**deployment_dict))

            return deployments_list
        return v
