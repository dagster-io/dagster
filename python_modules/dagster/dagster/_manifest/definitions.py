from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Literal, Sequence, Type, TypeVar

from pydantic import BaseModel

from dagster import _check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._manifest.executable import ManifestBackedExecutable
from dagster._manifest.schema import ExecutableManifest
from dagster._seven import is_subclass

# Define a type variable that can be any type.
TManifest = TypeVar("TManifest", bound=BaseModel)


def manifest_executable_kind(manifest_type: Type[ExecutableManifest]) -> str:
    # Looks like Python doesn't support argument types that must be a subclass and abide by a Protocol
    check.invariant(
        is_subclass(manifest_type, BaseModel), "Manifest type must be a Pydantic model."
    )
    model_fields = manifest_type.model_fields  # type: ignore
    kind_field = model_fields["kind"]
    check.invariant(
        kind_field.annotation.__origin__ == Literal,
        "Manifest executable schema must have kind field with Literal type.",
    )
    return kind_field.annotation.__args__[0]


class ManifestSource(Generic[TManifest]):
    def get_manifest(self) -> TManifest:
        raise NotImplementedError("Subclasses must implement this method.")


def definitions_from_executables(
    executables: List[ManifestBackedExecutable], resources: Dict[str, Any]
) -> Definitions:
    return Definitions(
        assets=[executable.to_assets_def() for executable in executables], resources=resources
    )


class ManifestFactory(Generic[TManifest], ABC):
    @abstractmethod
    def make_definitions(self, manifest: TManifest, resources: Dict[str, Any]) -> Definitions: ...


# Definitions factory from a list of executable manifests.
class ManifestBackedExecutableFactory(ManifestFactory[TManifest]):
    def __init__(self) -> None:
        for executable_type in self.executables():
            manifest_executable_schema_cls = executable_type.manifest_cls()
            if not manifest_executable_schema_cls:
                raise Exception(
                    f"Executable {executable_type.__name__} must have a manifest_cls method."
                )

    def make_definitions(self, manifest: TManifest, resources: Dict[str, Any]) -> Definitions:
        executables = manifest.executables  # type: ignore
        return self.from_executable_manifests(executables, resources)

    def from_executable_manifests(
        self, executable_manifests: Sequence[ExecutableManifest], resources: Dict[str, Any]
    ) -> Definitions:
        return definitions_from_executables(
            executables=[
                type(self).create_executable(executable_manifest)
                for executable_manifest in executable_manifests
            ],
            resources=resources,
        )

    @classmethod
    @abstractmethod
    def executables(cls) -> List[Type[ManifestBackedExecutable]]: ...

    @classmethod
    def create_executable(cls, manifest: ExecutableManifest) -> ManifestBackedExecutable:
        for executable_type in cls.executables():
            manifest_cls = executable_type.manifest_cls()
            check.invariant(
                is_subclass(manifest_cls, BaseModel), "Manifest type must be a Pydantic model."
            )
            check.invariant("kind" in manifest_cls.__fields__)  # type: ignore
            if manifest.kind == manifest_executable_kind(manifest_cls):
                return executable_type.create_from_manifest(manifest)

        raise Exception(f"Unknown kind {manifest.kind}.")
