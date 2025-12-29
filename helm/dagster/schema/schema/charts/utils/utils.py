from collections.abc import Mapping
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel as PydanticBaseModel,
    Field,
)


class SupportedKubernetes(str, Enum):
    V1_19 = "1.19.0"


class ConfigurableClass(PydanticBaseModel, extra="forbid"):
    module: str
    class_: str = Field(alias="class")
    config: dict


class BaseModel(PydanticBaseModel):
    class Config:
        """Pydantic currently does not support nullable required fields. Here, we use a workaround to
        allow this behavior.

        See https://github.com/samuelcolvin/pydantic/issues/1270#issuecomment-729555558
        """

        @staticmethod
        def schema_extra(schema, model):
            for prop, value in schema.get("properties", {}).items():
                # retrieve right field from alias or name
                field = next(x for x in model.model_fields.values() if x.alias == prop)
                if field.allow_none:
                    # only one type e.g. {'type': 'integer'}
                    if "type" in value:
                        value["anyOf"] = [{"type": value.pop("type")}]
                    # only one $ref e.g. from other model
                    elif "$ref" in value:
                        if issubclass(field.type_, PydanticBaseModel):
                            # add 'title' in schema to have the exact same behaviour as the rest
                            value["title"] = field.type_.__config__.title or field.type_.__name__
                        value["anyOf"] = [{"$ref": value.pop("$ref")}]
                    value["anyOf"].append({"type": "null"})


# Key used to mark Kubernetes definition references in the schema.
# These are converted to $ref values by the CLI when generating the final schema,
# embedding the actual definitions from the local kubernetes definitions file.
# The definitions are sourced from https://github.com/yannh/kubernetes-json-schema (Apache-2.0 License)
# and downloaded using helm/dagster/schema/scripts/update_kubernetes_definitions.py
KUBERNETES_REF_KEY = "$__kubernetes_ref"


def create_definition_ref(definition: str) -> dict[str, str]:
    """Create a placeholder reference to a Kubernetes schema definition.

    Returns a dict with a special key that will be converted to a proper $ref
    by the CLI during schema generation.
    """
    return {KUBERNETES_REF_KEY: definition}


def create_json_schema_conditionals(
    enum_type_to_config_name_mapping: dict[Enum, str],
) -> list[Mapping[str, Any]]:
    return [
        {
            "if": {
                "properties": {"type": {"const": enum_type}},
            },
            "then": {"properties": {"config": {"required": [config_name]}}},
        }
        for (enum_type, config_name) in enum_type_to_config_name_mapping.items()
    ]
