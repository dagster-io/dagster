import shutil
from abc import abstractmethod
from functools import cached_property
from pathlib import Path
from typing import Iterable, NamedTuple, Sequence

from dagster import AssetSpec, file_relative_path, multi_asset
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster._seven import import_module_from_path
from typing_extensions import Self

# Directory path
directory = Path(file_relative_path(__file__, "assets"))


class AssetMetadataHolder:
    def __init__(self, cls_instance) -> None:
        self.cls_instance = cls_instance

    @property
    def deps(self):
        if not hasattr(self.cls_instance, "deps"):
            return []

        return [
            AssetKey.from_user_string(dep_string)
            for dep_string in (getattr(self.cls_instance, "deps") or [])
        ]

    @property
    def description(self):
        if not hasattr(self.cls_instance, "description"):
            return None

        return getattr(self.cls_instance, "description") or None


import hashlib


def compute_file_hash(file_path, hash_algorithm="sha256"):
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
    if not hasattr(asset_metadata_cls, "deps"):
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


class PythonFileBasedAttrs(NamedTuple):
    file_path: Path
    op_name: str
    asset_spec: AssetSpec

    @classmethod
    def from_file_path(cls, file_path: Path) -> "PythonFileBasedAttrs":
        mod = import_module_from_path(file_path.stem, str(file_path.resolve()))
        attrs_obj = getattr(mod, "Attrs")
        assert attrs_obj
        parts = file_path.stem.split(".")
        asset_key = AssetKey(parts)
        return cls(
            file_path=file_path,
            op_name=parts[-1],
            asset_spec=AssetSpec(
                key=asset_key,
                deps=deps_from_metadata_cls(attrs_obj),
                description=build_description_from_python_file(file_path),
            ),
        )

    @property
    def python_file_path(self) -> str:
        return str(self.file_path.resolve())


class PythonFileBasedAsset:
    def __init__(self, attrs: PythonFileBasedAttrs):
        self.attrs = attrs

    def to_assets_def(self) -> AssetsDefinition:
        @multi_asset(specs=[self.attrs.asset_spec], name=self.attrs.op_name)
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
    def from_file_path(cls, file_path: Path) -> Self:
        return cls(PythonFileBasedAttrs.from_file_path(file_path))

    @classmethod
    def make_def(cls, file_path: Path) -> AssetsDefinition:
        return cls.from_file_path(file_path).to_assets_def()

    @classmethod
    def make_defs_from_folder(cls, cwd: Path, folder: Path) -> Sequence[AssetsDefinition]:
        assets_defs = []
        for file in (cwd / folder).iterdir():
            if file.suffix != ".py":
                continue

            assets_defs.append(cls.make_def(file))

        return assets_defs

    @abstractmethod
    def execute(
        self, context: AssetExecutionContext, subprocess_client: PipesSubprocessClient
    ) -> Iterable[PipesExecutionResult]: ...

    @classmethod
    @abstractmethod
    def build_asset(cls, attrs: PythonFileBasedAttrs) -> Self: ...




# class ThisAssetAttrs(PythonFileBasedAttrs):
#     @property
#     def tags(self) -> dict:
#         return {"tag1": "default_value"}


class ThisAsset(PythonFileBasedAsset):
    def execute(
        self, context: AssetExecutionContext, subprocess_client: PipesSubprocessClient
    ) -> Iterable[PipesExecutionResult]:
        results = subprocess_client.run(
            context=context,
            command=[self.python_executable_path, self.python_file_path],
        ).get_results()
        return results

    # @classmethod
    # def build_asset_attrs(cls) -> ThisAssetAttrs:
    #     return ThisAssetAttrs()

    @classmethod
    def build_asset(cls, attrs: PythonFileBasedAttrs) -> "ThisAsset":
        return ThisAsset(attrs)


defs = Definitions(
    assets=ThisAsset.make_defs_from_folder(Path.cwd(), Path("assets")),
    resources={"subprocess_client": PipesSubprocessClient()},
)

if __name__ == "__main__":
    defs.get_implicit_global_asset_job_def().execute_in_process()
