from enum import Enum
from typing import Dict, List

# pylint: disable=E0611
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra


class SupportedKubernetes(str, Enum):
    V1_15 = "1.15.0"
    V1_16 = "1.16.0"


class ConfigurableClass(PydanticBaseModel):
    module: str
    class_: str
    config: dict

    class Config:
        fields = {"class_": "class"}
        extra = Extra.forbid


class BaseModel(PydanticBaseModel):
    class Config:
        """
        Pydantic currently does not support nullable required fields. Here, we use a workaround to
        allow this behavior.

        See https://github.com/samuelcolvin/pydantic/issues/1270#issuecomment-729555558
        """

        @staticmethod
        def schema_extra(schema, model):
            for prop, value in schema.get("properties", {}).items():
                # retrieve right field from alias or name
                field = [x for x in model.__fields__.values() if x.alias == prop][0]
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


def create_definition_ref(definition: str, version: str = SupportedKubernetes.V1_15) -> str:
    return (
        f"https://kubernetesjsonschema.dev/v{version}/_definitions.json#/definitions/{definition}"
    )


def create_json_schema_conditionals(
    enum_type_to_config_name_mapping: Dict[Enum, str]
) -> List[dict]:
    return [
        {
            "if": {
                "properties": {"type": {"const": enum_type}},
            },
            "then": {"properties": {"config": {"required": [config_name]}}},
        }
        for (enum_type, config_name) in enum_type_to_config_name_mapping.items()
    ]
