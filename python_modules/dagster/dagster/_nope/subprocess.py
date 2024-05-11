import hashlib
import shutil
from functools import cached_property
from pathlib import Path
from typing import (
    Any,
    Iterable,
    Optional,
)

from dagster import (
    _check as check,
)
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.context import PipesExecutionResult
from dagster._core.pipes.subprocess import PipesSubprocessClient

from .project import NopeAssetManifest, NopeInvocationTarget, NopeInvocationTargetManifest


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


def build_description_from_python_file(file_path: Path) -> str:
    return (
        f"""Python file "{file_path.name}":
"""
        + "```\n"
        + file_path.read_text()
        + "\n```"
    )


class NopeSubprocessInvocationTarget(NopeInvocationTarget):
    class InvocationTargetManifest(NopeInvocationTargetManifest):
        @property
        def tags(self) -> dict:
            return {"kind": "python"}

        @cached_property
        def full_python_path(self) -> Path:
            check.invariant(self.full_manifest_path, "full_manifest_path must be set")
            assert self.full_manifest_path
            manifest_dir = self.full_manifest_path.resolve().parent
            if "script" not in self.full_manifest_obj:
                raise ValueError(
                    "No script key found in manifest file for subprocess invocation target"
                )
            return manifest_dir / Path(self.full_manifest_obj["script"])

    class AssetManifest(NopeAssetManifest):
        @property
        def invocation_target_python_path(self) -> Path:
            # TODO: Use generics to avoid type check?
            return check.not_none(
                check.inst(
                    self.invocation_target_manifest,
                    NopeSubprocessInvocationTarget.InvocationTargetManifest,
                ).python_script_path
            ).resolve()

        @property
        def code_version(self) -> Optional[str]:
            return compute_file_hash(self.invocation_target_python_path)

        @property
        def description(self) -> str:
            # TODO: pluggablize this
            if self.invocation_target_python_path:
                return build_description_from_python_file(self.invocation_target_python_path)

            return "No description available"

    @cached_property
    def python_executable_path(self) -> str:
        python_executable = shutil.which("python")
        if not python_executable:
            raise ValueError("Python executable not found.")
        return python_executable

    @property
    def full_str_python_path(self) -> str:
        # TODO: Use generics to avoid type check?
        return str(
            check.inst(
                self.target_manifest, NopeSubprocessInvocationTarget.InvocationTargetManifest
            ).python_script_path
        )

    def invoke(
        self, context: AssetExecutionContext, subprocess_client: PipesSubprocessClient
    ) -> Iterable[PipesExecutionResult]:
        command = [self.python_executable_path, self.full_str_python_path]
        return subprocess_client.run(context=context, command=command).get_results()
