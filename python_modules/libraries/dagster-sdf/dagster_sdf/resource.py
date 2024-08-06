import os
import shutil
import uuid
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

from dagster import AssetExecutionContext, ConfigurableResource, OpExecutionContext
from dagster._annotations import experimental, public
from dagster._utils.warnings import suppress_dagster_warnings
from pydantic import Field, validator

from .constants import (
    DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
    SDF_DAGSTER_OUTPUT_DIR,
    SDF_EXECUTABLE,
    SDF_WORKSPACE_YML,
)
from .dagster_sdf_translator import DagsterSdfTranslator, validate_opt_translator
from .sdf_cli_invocation import SdfCliInvocation
from .sdf_workspace import SdfWorkspace


@suppress_dagster_warnings
@experimental
class SdfCliResource(ConfigurableResource):
    """A resource used to execute sdf CLI commands.

    Attributes:
        workspace_dir (str): The path to the sdf workspace directory. This directory should contain a
            `workspace.sdf.yml`.
        global_config_flags (List[str]): A list of global flags configuration to pass to the sdf CLI
            invocation.
        sdf_executable (str): The path to the sdf executable. By default, this is `sdf`.
    """

    workspace_dir: str = Field(
        description=(
            "The path to the sdf workspace directory. This directory should contain a"
            " `workspace.sdf.yml`."
        ),
    )
    global_config_flags: List[str] = Field(
        default=[],
        description="A list of global flags configuration to pass to the sdf CLI invocation.",
    )
    sdf_executable: str = Field(
        default=SDF_EXECUTABLE,
        description="The path to the sdf executable.",
    )

    def __init__(
        self,
        workspace_dir: Union[str, Path, SdfWorkspace],
        global_config_flags: Optional[List[str]] = None,
        sdf_executable: str = SDF_EXECUTABLE,
        **kwargs,  # allow custom subclasses to add fields
    ):
        if isinstance(workspace_dir, SdfWorkspace):
            workspace_dir = workspace_dir.workspace_dir
        # static typing doesn't understand whats going on here, thinks these fields dont exist
        super().__init__(
            workspace_dir=workspace_dir,  # type: ignore
            global_config_flags=global_config_flags or [],  # type: ignore
            sdf_executable=sdf_executable,  # type: ignore
            **kwargs,
        )

    @validator("workspace_dir", pre=True)
    def convert_path_to_str(cls, v: Any) -> Any:
        """Validate that the path is converted to a string."""
        if isinstance(v, Path):
            resolved_path = cls._validate_absolute_path_exists(v)

            absolute_path = Path(v).absolute()
            try:
                resolved_path = absolute_path.resolve(strict=True)
            except FileNotFoundError:
                raise ValueError(f"The absolute path of '{v}' ('{absolute_path}') does not exist")
            return os.fspath(resolved_path)

        return v

    @validator("workspace_dir")
    def validate_workspace_dir(cls, project_dir: str) -> str:
        resolved_workspace_dir = cls._validate_absolute_path_exists(project_dir)

        cls._validate_path_contains_file(
            path=resolved_workspace_dir,
            file_name=SDF_WORKSPACE_YML,
            error_message=(
                f"{resolved_workspace_dir} does not contain an {SDF_WORKSPACE_YML} file. Please"
                " specify a valid path to an sdf workspace."
            ),
        )

        return os.fspath(resolved_workspace_dir)

    @validator("sdf_executable")
    def validate_sdf_executable(cls, sdf_executable: str) -> str:
        resolved_sdf_executable = shutil.which(sdf_executable)
        if not resolved_sdf_executable:
            raise ValueError(
                f"The sdf executable '{sdf_executable}' does not exist. Please specify a valid"
                " path to an sdf executable."
            )

        return sdf_executable

    @public
    def cli(
        self,
        args: Sequence[str],
        *,
        target_dir: Optional[Path] = None,
        environment: str = DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
        raise_on_error: bool = True,
        dagster_sdf_translator: Optional[DagsterSdfTranslator] = None,
        context: Optional[Union[OpExecutionContext, AssetExecutionContext]] = None,
    ) -> SdfCliInvocation:
        """Create a subprocess to execute an sdf CLI command.

        Args:
            args (Sequence[str]): The sdf CLI command to execute.
            target_dir (Optional[Path]): The path to the target directory.
            environment (str): The environment to use. Defaults to "dbg".
            raise_on_error (bool): Whether to raise an exception if the sdf CLI command fails.
            context (Optional[Union[OpExecutionContext, AssetExecutionContext]]): The execution context from within `@sdf_assets`.
                If an AssetExecutionContext is passed, its underlying OpExecutionContext will be used.

        Returns:
            SdfCliInvocation: A invocation instance that can be used to retrieve the output of the
                sdf CLI command.
        """
        dagster_sdf_translator = validate_opt_translator(dagster_sdf_translator)
        dagster_sdf_translator = dagster_sdf_translator or DagsterSdfTranslator()
        context = (
            context.op_execution_context if isinstance(context, AssetExecutionContext) else context
        )

        # Pass the current environment variables to the sdf CLI invocation.
        env = os.environ.copy()

        environment_args = ["--environment", environment]
        target_path = target_dir or self._get_unique_target_path(context=context)
        target_args = ["--target-dir", str(target_path)]
        log_level_args = ["--log-level", "info"]

        # Ensure that the target_dir exists
        target_path.mkdir(parents=True, exist_ok=True)

        args = [
            self.sdf_executable,
            *self.global_config_flags,
            *log_level_args,
            *args,
            *environment_args,
            *target_args,
        ]

        return SdfCliInvocation.run(
            args=args,
            env=env,
            workspace_dir=Path(self.workspace_dir),
            target_dir=target_path,
            environment=environment,
            dagster_sdf_translator=dagster_sdf_translator,
            raise_on_error=raise_on_error,
            context=context,
        )

    @classmethod
    def _validate_absolute_path_exists(cls, path: Union[str, Path]) -> Path:
        absolute_path = Path(path).absolute()
        try:
            resolved_path = absolute_path.resolve(strict=True)
        except FileNotFoundError:
            raise ValueError(f"The absolute path of '{path}' ('{absolute_path}') does not exist")

        return resolved_path

    @classmethod
    def _validate_path_contains_file(cls, path: Path, file_name: str, error_message: str):
        if not path.joinpath(file_name).exists():
            raise ValueError(error_message)

    def _get_unique_target_path(self, *, context: Optional[OpExecutionContext]) -> Path:
        """Get a unique target path for the sdf CLI invocation.

        Args:
            context (Optional[OpExecutionContext]): The execution context.

        Returns:
            str: A unique target path for the sdf CLI invocation.
        """
        unique_id = str(uuid.uuid4())[:7]
        path = unique_id
        if context:
            path = f"{context.op.name}-{context.run.run_id[:7]}-{unique_id}"

        current_output_path = Path(self.workspace_dir).joinpath(SDF_DAGSTER_OUTPUT_DIR)

        return current_output_path.joinpath(path)
