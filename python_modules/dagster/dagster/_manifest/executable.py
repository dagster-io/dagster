from abc import abstractmethod
from typing import (
    Type,
)

from dagster._core.definitions.factory.executable import AssetGraphExecutable

from .schema import ExecutableManifest


class ManifestBackedExecutable(AssetGraphExecutable):
    def __init__(self, *, manifest, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manifest = manifest

    @classmethod
    @abstractmethod
    def manifest_cls(cls) -> Type[ExecutableManifest]: ...

    @classmethod
    @abstractmethod
    def create_from_manifest(cls, manifest: ExecutableManifest) -> "ManifestBackedExecutable": ...
