from typing import Any, TypedDict


class SerializationModule(TypedDict, total=False):
    """W&B Artifacts IO Manager configuration of the serialization module. Useful for type checking."""

    name: str
    parameters: dict[str, Any]


class WandbArtifactConfiguration(TypedDict, total=False):
    """W&B Artifacts IO Manager configuration. Useful for type checking."""

    name: str
    type: str
    description: str
    aliases: list[str]
    add_dirs: list[dict[str, Any]]
    add_files: list[dict[str, Any]]
    add_references: list[dict[str, Any]]
    serialization_module: SerializationModule
    partitions: dict[str, dict[str, Any]]
