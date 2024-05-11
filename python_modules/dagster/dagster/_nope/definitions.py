from typing import Any, Dict, Generic, Type, TypeVar

from dagster._core.definitions.definitions_class import Definitions

# Define a type variable that can be any type.
T = TypeVar("T")


class ManifestSource(Generic[T]):
    def get_manifest(self) -> T:
        raise NotImplementedError("Subclasses must implement this method.")


class InMemoryManifestSource(ManifestSource[T]):
    def __init__(self, manifest: T):
        self.manifest = manifest

    def get_manifest(self) -> T:
        return self.manifest


class DefinitionsBuilder(Generic[T]):
    @classmethod
    def build(cls, manifest: T, resources: Dict[str, Any]) -> Definitions:
        raise NotImplementedError("Subclasses must implement this method.")


def make_nope_definitions(
    manifest_source: ManifestSource,
    defs_builder_cls: Type,
    resources: Dict[str, Any],
) -> Definitions:
    return defs_builder_cls.build(manifest=manifest_source.get_manifest(), resources=resources)
