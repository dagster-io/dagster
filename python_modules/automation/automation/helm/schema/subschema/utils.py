from enum import Enum


class SupportedKubernetes(str, Enum):
    V1_15 = "1.15.0"
    V1_16 = "1.16.0"


def create_definition_ref(definition: str, version: str = SupportedKubernetes.V1_15) -> str:
    return (
        f"https://kubernetesjsonschema.dev/v{version}/_definitions.json#/definitions/{definition}"
    )
