import hashlib
import shutil
from abc import abstractmethod
from functools import cached_property
from pathlib import Path
from typing import Any, Iterable, List, Sequence

from dagster import AssetSpec, file_relative_path, multi_asset
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster._seven import import_module_from_path
from typing_extensions import Self

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


def deps_from_metadata_cls(asset_metadata_cls) -> Sequence[CoercibleToAssetDep]:
    if not asset_metadata_cls or not hasattr(asset_metadata_cls, "deps"):
        return []

    return [
        AssetKey.from_user_string(dep) if isinstance(dep, str) else dep
        for dep in (getattr(asset_metadata_cls, "deps") or [])
    ]


def build_description_from_python_file(file_path: Path) -> str:
    return (
        f"""Python file "{file_path.name}":
"""
        + "```\n"
        + file_path.read_text()
        + "\n```"
    )


class PipesScriptManifest:
    file_path: Path
    asset_spec: AssetSpec

    def __init__(self, group_folder: Path, full_python_path: Path) -> None:
        mod = import_module_from_path(full_python_path.stem, str(full_python_path.resolve()))
        self.group_folder = group_folder
        self.full_python_path = full_python_path
        self.attrs_obj = getattr(mod, "Attrs") if hasattr(mod, "Attrs") else None

    @property
    def code_version(self) -> str:
        return compute_file_hash(self.full_python_path)

    @property
    def deps(self) -> Sequence[CoercibleToAssetDep]:
        return deps_from_metadata_cls(self.attrs_obj)

    @property
    def description(self) -> str:
        return build_description_from_python_file(self.full_python_path)

    @property
    def asset_key(self) -> CoercibleToAssetKey:
        return AssetKey([self.group_name] + self.file_name_parts)

    @property
    def file_name_parts(self) -> List[str]:
        return self.full_python_path.stem.split(".")

    @property
    def op_name(self) -> str:
        return self.file_name_parts[-1]

    @property
    def group_name(self) -> str:
        return self.group_folder.name

    @property
    def tags(self) -> dict:
        return {}

    @property
    def asset_specs(self) -> Sequence[AssetSpec]:
        return [
            AssetSpec(
                key=self.asset_key,
                deps=self.deps,
                description=self.description,
                group_name=self.group_name,
                tags=self.tags,
            )
        ]

    @property
    def python_file_path(self) -> str:
        return str(self.full_python_path.resolve())


class PipesScript:
    def __init__(self, attrs: PipesScriptManifest):
        self._attrs = attrs

    @property
    def attrs(self) -> PipesScriptManifest:
        return self._attrs

    def to_assets_def(self) -> AssetsDefinition:
        @multi_asset(specs=self.attrs.asset_specs, name=self.attrs.op_name)
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
    def python_file_path(self) -> str:
        return self.attrs.python_file_path

    @classmethod
    def from_file_path(cls, group_folder: Path, full_python_path: Path) -> Self:
        return cls(PipesScriptManifest(group_folder, full_python_path))

    @classmethod
    def make_def(cls, group_folder: Path, full_python_path: Path) -> AssetsDefinition:
        return cls.from_file_path(
            group_folder=group_folder, full_python_path=full_python_path
        ).to_assets_def()

    @classmethod
    def make_defs_from_group_folder(
        cls, cwd: Path, group_folder: Path
    ) -> Sequence[AssetsDefinition]:
        assets_defs = []
        for full_python_path in (cwd / group_folder).iterdir():
            if full_python_path.suffix != ".py":
                continue

            assets_defs.append(
                cls.make_def(group_folder=group_folder, full_python_path=full_python_path)
            )

        return assets_defs

    @abstractmethod
    def execute(
        self, context: AssetExecutionContext, subprocess_client: PipesSubprocessClient
    ) -> Iterable[PipesExecutionResult]: ...

    @classmethod
    @abstractmethod
    def build_pipes_script(cls, attrs: PipesScriptManifest) -> Self: ...


class ProjectFooBarScriptManifest(PipesScriptManifest):
    @property
    def tags(self) -> dict:
        return {"tag1": "default_value"}


class ProjectFooBarScript(PipesScript):
    def execute(
        self, context: AssetExecutionContext, subprocess_client: PipesSubprocessClient
    ) -> Iterable[PipesExecutionResult]:
        results = subprocess_client.run(
            context=context,
            command=[self.python_executable_path, self.python_file_path],
        ).get_results()
        return results

    @property
    def attrs(self) -> ProjectFooBarScriptManifest:
        return super().attrs  # type: ignore

    @classmethod
    def build_pipes_script(cls, attrs: ProjectFooBarScriptManifest) -> "ProjectFooBarScript":
        return ProjectFooBarScript(attrs)


defs = Definitions(
    assets=ProjectFooBarScript.make_defs_from_group_folder(Path.cwd(), Path("assets/some_group")),
    resources={"subprocess_client": PipesSubprocessClient()},
)

if __name__ == "__main__":
    defs.get_implicit_global_asset_job_def().execute_in_process()
