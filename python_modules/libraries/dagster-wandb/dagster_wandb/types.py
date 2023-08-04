import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Any, Dict, List


class SerializationModule(TypedDict, total=False):
    """W&B Artifacts IO Manager configuration of the serialization module. Useful for type checking."""

    name: str
    parameters: Dict[str, Any]


class WandbArtifactConfiguration(TypedDict, total=False):
    """W&B Artifacts IO Manager configuration. Useful for type checking."""

    name: str
    type: str
    description: str
    aliases: List[str]
    add_dirs: List[Dict[str, Any]]
    add_files: List[Dict[str, Any]]
    add_references: List[Dict[str, Any]]
    serialization_module: SerializationModule
    partitions: Dict[str, Dict[str, Any]]
