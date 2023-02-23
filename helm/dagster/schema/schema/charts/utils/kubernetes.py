from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Extra

from .utils import (
    BaseModel as BaseModelWithNullableRequiredFields,
    create_definition_ref,
)


class Annotations(BaseModel):
    __root__: Dict[str, str]

    class Config:
        schema_extra = {
            "$ref": create_definition_ref(
                "io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta/properties/annotations"
            )
        }


class Labels(BaseModel):
    class Config:
        schema_extra = {
            "$ref": create_definition_ref(
                "io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta/properties/labels"
            )
        }


class PullPolicy(str, Enum):
    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"


class Image(BaseModelWithNullableRequiredFields):
    repository: str
    tag: Optional[Union[str, int]]
    pullPolicy: PullPolicy

    @property
    def name(self) -> str:
        return f"{self.repository}:{self.tag}" if self.tag else self.repository


class ExternalImage(Image):
    tag: str


class Service(BaseModel):
    type: str
    port: int
    annotations: Optional[Annotations]

    class Config:
        extra = Extra.forbid


class NodeSelector(BaseModel):
    __root__: Dict[str, str]

    class Config:
        schema_extra = {
            "$ref": create_definition_ref("io.k8s.api.core.v1.PodSpec/properties/nodeSelector")
        }


class Affinity(BaseModel):
    __root__: Dict[str, Any]

    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.Affinity")}


class Tolerations(BaseModel):
    __root__: List[Dict[str, Any]]

    class Config:
        schema_extra = {
            "$ref": create_definition_ref("io.k8s.api.core.v1.PodSpec/properties/tolerations")
        }


class PodSecurityContext(BaseModel):
    __root__: Dict[str, Any]

    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.PodSecurityContext")}


class SecurityContext(BaseModel):
    __root__: Dict[str, Any]

    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.SecurityContext")}


class InitContainer(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.Container")}


class Resources(BaseModel):
    __root__: Dict[str, Any]

    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.ResourceRequirements")}


class LivenessProbe(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.Probe")}


class ReadinessProbe(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.Probe")}


class StartupProbe(BaseModel):
    enabled: bool = True

    class Config:
        schema_extra = {
            "$ref": create_definition_ref("io.k8s.api.core.v1.Probe"),
        }


class SecretRef(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.LocalObjectReference")}


class SecretEnvSource(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.SecretEnvSource")}


class ConfigMapEnvSource(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.ConfigMapEnvSource")}


class VolumeMount(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.VolumeMount")}


class Volume(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.Volume")}


class ResourceRequirements(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.ResourceRequirements")}


class EnvVar(BaseModel):
    class Config:
        schema_extra = {"$ref": create_definition_ref("io.k8s.api.core.v1.EnvVar")}
