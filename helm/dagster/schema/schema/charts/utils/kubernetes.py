from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, RootModel

from schema.charts.utils.utils import (
    BaseModel as BaseModelWithNullableRequiredFields,
    create_definition_ref,
)


class Annotations(RootModel[dict[str, str]]):
    model_config = {
        "json_schema_extra": {
            "$ref": create_definition_ref(
                "io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta/properties/annotations"
            )
        }
    }


class Labels(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "$ref": create_definition_ref(
                "io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta/properties/labels"
            )
        },
    }


class PullPolicy(str, Enum):
    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"


class Image(BaseModelWithNullableRequiredFields):
    repository: str
    tag: Optional[Union[str, int]] = None
    pullPolicy: PullPolicy

    @property
    def name(self) -> str:
        return f"{self.repository}:{self.tag}" if self.tag else self.repository


class ExternalImage(Image):
    tag: str


class Service(BaseModel, extra="forbid"):
    type: str
    port: int
    annotations: Optional[Annotations] = None


class NodeSelector(RootModel[dict[str, str]]):
    model_config = {
        "json_schema_extra": {
            "extra": "allow",
            "$ref": create_definition_ref("io.k8s.api.core.v1.PodSpec/properties/nodeSelector"),
        }
    }


class Affinity(RootModel[dict[str, Any]]):
    model_config = {
        "json_schema_extra": {"$ref": create_definition_ref("io.k8s.api.core.v1.Affinity")}
    }


class Tolerations(RootModel[list[dict[str, Any]]]):
    model_config = {
        "json_schema_extra": {
            "$ref": create_definition_ref("io.k8s.api.core.v1.PodSpec/properties/tolerations")
        }
    }


class PodSecurityContext(RootModel[dict[str, Any]]):
    model_config = {
        "json_schema_extra": {
            "$ref": create_definition_ref("io.k8s.api.core.v1.PodSecurityContext")
        }
    }


class SecurityContext(
    RootModel[dict[str, Any]],
    json_schema_extra={"$ref": create_definition_ref("io.k8s.api.core.v1.SecurityContext")},
):
    pass


class InitContainer(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {"$ref": create_definition_ref("io.k8s.api.core.v1.Container")},
    }


class Resources(RootModel[dict[str, Any]]):
    model_config = {
        "json_schema_extra": {
            "$ref": create_definition_ref("io.k8s.api.core.v1.ResourceRequirements")
        }
    }


class LivenessProbe(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {"$ref": create_definition_ref("io.k8s.api.core.v1.Probe")},
    }


class ReadinessProbe(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {"$ref": create_definition_ref("io.k8s.api.core.v1.Probe")},
    }


class StartupProbe(BaseModel):
    enabled: bool = True

    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "$ref": create_definition_ref("io.k8s.api.core.v1.Probe"),
        },
    }


class SecretRef(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "$ref": create_definition_ref("io.k8s.api.core.v1.LocalObjectReference")
        },
    }


class SecretEnvSource(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {"$ref": create_definition_ref("io.k8s.api.core.v1.SecretEnvSource")},
    }


class ConfigMapEnvSource(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "$ref": create_definition_ref("io.k8s.api.core.v1.ConfigMapEnvSource")
        },
    }


class VolumeMount(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {"$ref": create_definition_ref("io.k8s.api.core.v1.VolumeMount")},
    }


class Volume(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {"$ref": create_definition_ref("io.k8s.api.core.v1.Volume")},
    }


class ResourceRequirements(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "$ref": create_definition_ref("io.k8s.api.core.v1.ResourceRequirements")
        },
    }


class EnvVar(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {"$ref": create_definition_ref("io.k8s.api.core.v1.EnvVar")},
    }


class Container(BaseModel):
    model_config = {
        "extra": "allow",
        "json_schema_extra": {"$ref": create_definition_ref("io.k8s.api.core.v1.Container")},
    }
