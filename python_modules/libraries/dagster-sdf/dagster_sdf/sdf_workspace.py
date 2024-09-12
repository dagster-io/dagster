import logging
import os
from pathlib import Path
from typing import Optional, Sequence, Union

from dagster._annotations import experimental
from dagster._model import DagsterModel
from dagster._utils import run_with_concurrent_update_guard
from dagster._utils.warnings import suppress_dagster_warnings

from dagster_sdf.constants import DEFAULT_SDF_WORKSPACE_ENVIRONMENT, SDF_EXECUTABLE, SDF_TARGET_DIR
from dagster_sdf.errors import (
    DagsterSdfInformationSchemaNotFoundError,
    DagsterSdfWorkspaceNotFoundError,
    DagsterSdfWorkspaceYmlFileNotFoundError,
)
from dagster_sdf.sdf_information_schema import SdfInformationSchema

logger = logging.getLogger("dagster-sdf.artifacts")


def using_dagster_dev() -> bool:
    return bool(os.getenv("DAGSTER_IS_DEV_CLI"))


@experimental
class SdfWorkspacePreparer:
    def on_load(self, workspace: "SdfWorkspace") -> None:
        """Invoked when SdfWorkspace is instantiated with this preparer."""

    def prepare(self, workspace: "SdfWorkspace") -> None:
        """Called explictly to compile the workspace."""

    def using_dagster_dev(self) -> bool:
        return using_dagster_dev()

    def compile_on_load_opt_in(self) -> bool:
        return bool(os.getenv("DAGSTER_SDF_COMPILE_ON_LOAD"))


@experimental
class DagsterSdfWorkspacePreparer(SdfWorkspacePreparer):
    def __init__(
        self,
        generate_cli_args: Optional[Sequence[str]] = None,
    ):
        """The default SdfWorkspacePreparer, this handler provides an experience of:
            * During development, rerun compile to pick up any changes.
            * When deploying, expect the outcome of compile to reduce start-up time.

        Args:
            generate_cli_args (Sequence[str]):
                The arguments to pass to the sdf cli to prepare the workspace.
                Default: ["compile", "--save==table-deps,info-schema"]
        """
        self._generate_cli_args = generate_cli_args or [
            "compile",
            "--save",
            "table-deps,info-schema",
        ]

    def on_load(self, workspace: "SdfWorkspace"):
        if self.using_dagster_dev() or self.compile_on_load_opt_in():
            self.prepare(workspace)
            information_schema = SdfInformationSchema(
                workspace_dir=workspace.workspace_dir,
                target_dir=workspace.target_dir,
                environment=workspace.environment,
            )
            if not information_schema.is_parsed():
                raise DagsterSdfInformationSchemaNotFoundError(
                    f"Sdf Information Schema was not generated correctly at expected path {information_schema.information_schema_dir} "
                    f"after running '{self.prepare.__qualname__}'. Ensure the implementation respects "
                    "all Sdf Workspace properties."
                )

    def prepare(self, workspace: "SdfWorkspace") -> None:
        output_dir = workspace.target_dir.joinpath(SDF_TARGET_DIR, workspace.environment)
        run_with_concurrent_update_guard(
            output_dir,
            self._prepare_workspace,
            workspace=workspace,
        )

    def _prepare_workspace(self, workspace: "SdfWorkspace") -> None:
        from dagster_sdf.resource import SdfCliResource

        (
            SdfCliResource(workspace_dir=workspace)
            .cli(
                self._generate_cli_args,
                target_dir=workspace.target_dir,
                environment=workspace.environment,
                raise_on_error=False,
            )
            .wait()
        )


@suppress_dagster_warnings
@experimental
class SdfWorkspace(DagsterModel):
    """The SdfWorkspace is a representation of an sdf workspace that can be compiled and executed.

    Args:
    workspace_dir (Union[str, Path]):
        The directory of the sdf workspace.
    target_dir (Union[str, Path]):
        The directory, relative to the workspace directory, to target and output artifacts.
        Default: "sdf_dagster_target"
    environment (str):
        The environment to use for compilation and execution. Default: "dbg"
    workspace_preparer (Optional[SdfWorkspacePreparer]):
        A object for ensuring that the sdf workspace is in the right state at the right times.
        Default: DagsterSdfWorkspacePreparer
    sdf_executable (str):
        The path/name of the sdf executable to use. Default: "sdf"
    """

    workspace_dir: Path
    target_dir: Path
    environment: str
    workspace_preparer: SdfWorkspacePreparer
    sdf_executable: str

    def __init__(
        self,
        workspace_dir: Union[str, Path],
        *,
        target_dir: Union[str, Path] = Path(
            ""
        ),  # TODO: This should default to `sdftarget` but it will cause a double-up of `sdftarget` in the path
        environment: str = DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
        workspace_preparer: SdfWorkspacePreparer = DagsterSdfWorkspacePreparer(),
        sdf_executable: str = SDF_EXECUTABLE,
    ):
        workspace_dir = Path(workspace_dir)
        if not workspace_dir.exists():
            raise DagsterSdfWorkspaceNotFoundError(f"workspace_dir {workspace_dir} does not exist.")

        target_dir = workspace_dir.joinpath(target_dir)

        sdf_workspace_yml_path = workspace_dir.joinpath("workspace.sdf.yml")
        if not sdf_workspace_yml_path.exists():
            raise DagsterSdfWorkspaceYmlFileNotFoundError(
                f"Did not find workspace.sdf.yml at expected path {sdf_workspace_yml_path}. "
                f"Ensure the specified workspace directory respects all sdf workspace requirements."
            )

        super().__init__(
            workspace_dir=workspace_dir,
            target_dir=target_dir,
            environment=environment,
            workspace_preparer=workspace_preparer,
            sdf_executable=sdf_executable,
        )
        if workspace_preparer:
            workspace_preparer.on_load(self)
