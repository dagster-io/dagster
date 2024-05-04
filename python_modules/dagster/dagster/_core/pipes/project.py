import hashlib
import shutil
from abc import abstractmethod
from functools import cached_property
from pathlib import Path
from typing import Any, Iterable, List, Sequence, Type

import yaml
from typing_extensions import Self

from dagster import AssetSpec, file_relative_path, multi_asset
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.subprocess import PipesSubprocessClient

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# Directory path
directory = Path(file_relative_path(__file__, "assets"))


def compute_file_hash(file_path, hash_algorithm="sha256") -> Any:
    # Initialize the hash object
    hash_object = hashlib.new(hash_algorithm)

    # Open the file in binary mode and read its contents
    with open(file_path, "rb") as file:
        # Update the hash object with the file contents
        while chunk := file.read(4096):  # Read the file in chunks to conserve memory
            hash_object.update(chunk)

    # Get the hexadecimal digest of the hash
    file_hash = hash_object.hexdigest()
    return file_hash


def deps_from_metadata_cls(raw_manifest_obj: dict) -> Sequence[CoercibleToAssetDep]:
    if not raw_manifest_obj or "deps" not in raw_manifest_obj:
        return []

    return [
        AssetKey.from_user_string(dep) if isinstance(dep, str) else dep
        for dep in raw_manifest_obj["deps"]
    ]


def build_description_from_python_file(file_path: Path) -> str:
    return (
        f"""Python file "{file_path.name}":
"""
        + "```\n"
        + file_path.read_text()
        + "\n```"
    )


class PipesScriptAssetManifest:
    def __init__(
        self,
        manifest_obj,
        full_python_path: Path,
        group_folder: Path,
        asset_key_parts: List[str],
    ) -> None:
        self.manifest_obj = manifest_obj or {}
        self.full_python_path = full_python_path
        self.group_folder = group_folder
        self.asset_key_parts = asset_key_parts

    @property
    def code_version(self) -> str:
        return compute_file_hash(self.full_python_path)

    @property
    def deps(self) -> Sequence[CoercibleToAssetDep]:
        return deps_from_metadata_cls(self.manifest_obj)

    @property
    def description(self) -> str:
        return build_description_from_python_file(self.full_python_path)

    @property
    def asset_key(self) -> CoercibleToAssetKey:
        return AssetKey([self.group_name] + self.asset_key_parts)

    @property
    def file_name_parts(self) -> List[str]:
        return self.full_python_path.stem.split(".")

    @property
    def group_name(self) -> str:
        return self.group_folder.name

    @property
    def tags(self) -> dict:
        return self.manifest_obj.get("tags", {})

    @property
    def metadata(self) -> dict:
        return self.manifest_obj.get("metadata", {})

    @property
    def owners(self) -> List[str]:
        return self.manifest_obj.get("owners", [])

    @property
    def asset_spec(self) -> AssetSpec:
        return AssetSpec(
            key=self.asset_key,
            deps=self.deps,
            description=self.description,
            group_name=self.group_name,
            tags=self.tags,
            metadata=self.metadata,
            owners=self.owners,
        )


class PipesScriptManifest:
    file_path: Path
    asset_spec: AssetSpec

    def __init__(
        self,
        *,
        group_folder: Path,
        full_python_path: Path,
        full_manifest_path: Path,
        asset_manifest_class: Type,
    ) -> None:
        self.group_folder = group_folder
        self.full_python_path = full_python_path
        self.manifest_object = yaml.load(full_manifest_path.read_text(), Loader=Loader)
        self.asset_manifest_class = asset_manifest_class

    @property
    def asset_manifests(self) -> Sequence[PipesScriptAssetManifest]:
        if self.manifest_object and "assets" in self.manifest_object:
            list_of_single_key_dicts = self.manifest_object["assets"]

            asset_manifests = []
            for single_key_dict in list_of_single_key_dicts:
                if len(single_key_dict) != 1:
                    raise ValueError("Each asset manifest must have exactly one key.")
                asset_name, raw_asset_manifest = next(iter(single_key_dict.items()))
                asset_manifests.append(
                    self.asset_manifest_class(
                        manifest_obj=raw_asset_manifest,
                        full_python_path=self.full_python_path,
                        group_folder=self.group_folder,
                        asset_key_parts=asset_name.split("."),
                    )
                )
            return asset_manifests
        else:
            return [
                self.asset_manifest_class(
                    self.manifest_object,
                    self.full_python_path,
                    self.group_folder,
                    asset_key_parts=self.full_python_path.stem.split("."),
                )
            ]

    @property
    def file_name_parts(self) -> List[str]:
        return self.full_python_path.stem.split(".")

    @property
    def op_name(self) -> str:
        return self.file_name_parts[-1]

    @property
    def tags(self) -> dict:
        return {}

    @property
    def asset_specs(self) -> Sequence[AssetSpec]:
        return [asset_manifest.asset_spec for asset_manifest in self.asset_manifests]

    @property
    def metadata(self) -> dict:
        return {}


class PipesScript:
    def __init__(self, script_manifest: PipesScriptManifest):
        self._script_manifest = script_manifest

    @property
    def script_manifest(self) -> PipesScriptManifest:
        return self._script_manifest

    @classmethod
    def asset_manifest_class(cls) -> Type:
        return PipesScriptAssetManifest

    @classmethod
    def script_manifest_class(cls) -> Type:
        return PipesScriptManifest

    def to_assets_def(self) -> AssetsDefinition:
        @multi_asset(
            specs=self.script_manifest.asset_specs,
            name=self.script_manifest.op_name,
            op_tags=self.script_manifest.tags,
        )
        def _pipes_asset(context: AssetExecutionContext, subprocess_client: PipesSubprocessClient):
            return self.execute(context, subprocess_client)

        return _pipes_asset

    @cached_property
    def python_executable_path(self) -> str:
        python_executable = shutil.which("python")
        if not python_executable:
            raise ValueError("Python executable not found.")
        return python_executable

    @property
    def python_script_path(self) -> str:
        return str(self.script_manifest.full_python_path.resolve())

    @classmethod
    def from_file_path(
        cls, group_folder: Path, full_python_path: Path, full_yaml_path: Path
    ) -> Self:
        return cls(
            cls.script_manifest_class()(
                group_folder=group_folder,
                full_python_path=full_python_path,
                full_manifest_path=full_yaml_path,
                asset_manifest_class=cls.asset_manifest_class(),
            )
        )

    @classmethod
    def make_def(
        cls, group_folder: Path, full_python_path: Path, full_yaml_path: Path
    ) -> AssetsDefinition:
        return cls.from_file_path(
            group_folder=group_folder,
            full_python_path=full_python_path,
            full_yaml_path=full_yaml_path,
        ).to_assets_def()

    @classmethod
    def make_pipes_project_defs(
        cls, cwd: Path, top_level_folder: Path
    ) -> Sequence[AssetsDefinition]:
        assets_defs = []
        for group_folder in (cwd / top_level_folder).iterdir():
            if not group_folder.is_dir():
                continue

            # for asset_def in cls.make_defs_from_group_folder(cwd, group_dir):
            #     yield asset_def

            yaml_files = {}
            python_files = {}
            for full_path in (cwd / group_folder).iterdir():
                if full_path.suffix == ".yaml":
                    yaml_files[full_path.stem] = full_path
                elif full_path.suffix == ".py":
                    python_files[full_path.stem] = full_path

            for stem_name in set(yaml_files) & set(python_files):
                assets_defs.append(
                    cls.make_def(
                        group_folder=group_folder,
                        full_python_path=python_files[stem_name],
                        full_yaml_path=yaml_files[stem_name],
                    )
                )

        return assets_defs

    @abstractmethod
    def execute(
        self, context: AssetExecutionContext, subprocess_client: PipesSubprocessClient
    ) -> Iterable[PipesExecutionResult]: ...

    @classmethod
    @abstractmethod
    def build_pipes_script(cls, attrs: PipesScriptManifest) -> Self: ...
