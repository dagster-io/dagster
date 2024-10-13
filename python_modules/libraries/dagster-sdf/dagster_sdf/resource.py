import os
import re
import shutil
import subprocess
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    ConfigurableResource,
    DagsterInvariantViolationError,
    OpExecutionContext,
    get_dagster_logger,
)
from dagster._annotations import experimental, public
from dagster._core.errors import DagsterInvalidPropertyError
from dagster._utils.warnings import suppress_dagster_warnings
from pydantic import Field, validator

from dagster_sdf.asset_utils import dagster_name_fn, get_test_prefix
from dagster_sdf.constants import (
    DAGSTER_SDF_CATALOG_NAME,
    DAGSTER_SDF_DIALECT,
    DAGSTER_SDF_SCHEMA_NAME,
    DAGSTER_SDF_TABLE_ID,
    DAGSTER_SDF_TABLE_NAME,
    DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
    SDF_DAGSTER_OUTPUT_DIR,
    SDF_EXECUTABLE,
    SDF_WORKSPACE_YML,
)
from dagster_sdf.dagster_sdf_translator import DagsterSdfTranslator, validate_opt_translator
from dagster_sdf.sdf_cli_invocation import SdfCliInvocation
from dagster_sdf.sdf_version import SDF_VERSION_LOWER_BOUND, SDF_VERSION_UPPER_BOUND
from dagster_sdf.sdf_workspace import SdfWorkspace

logging = get_dagster_logger()


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
        self._validate_sdf_version()
        dagster_sdf_translator = validate_opt_translator(dagster_sdf_translator)
        assets_def: Optional[AssetsDefinition] = None
        with suppress(DagsterInvalidPropertyError):
            assets_def = context.assets_def if context else None

        context = (
            context.op_execution_context if isinstance(context, AssetExecutionContext) else context
        )

        dagster_sdf_translator = dagster_sdf_translator or DagsterSdfTranslator()
        run_args = []
        # If the context and assets_def are not None, then we need to pass in the selected targets
        # to the sdf CLI invocation.
        if context and assets_def is not None:
            run_args.append(
                "--targets-only"
            )  # This flag is used to only run the selected targets (and not upstreams)
            selected_output_names = context.selected_output_names
            for asset_key, asset_metadata in assets_def.metadata_by_key.items():
                asset_output_name = dagster_name_fn(
                    asset_key.path[0], asset_key.path[1], asset_key.path[2]
                )
                # Check if this output is expected, if so, add the table_id and optionally the expected test name to the run_args
                if selected_output_names and asset_output_name in selected_output_names:
                    table_id: Optional[str] = asset_metadata.get(DAGSTER_SDF_TABLE_ID)
                    catalog: Optional[str] = asset_metadata.get(DAGSTER_SDF_CATALOG_NAME)
                    schema: Optional[str] = asset_metadata.get(DAGSTER_SDF_SCHEMA_NAME)
                    table_name: Optional[str] = asset_metadata.get(DAGSTER_SDF_TABLE_NAME)
                    table_dialect: Optional[str] = asset_metadata.get(DAGSTER_SDF_DIALECT)
                    # If any of the metadata is missing, raise an error
                    if (
                        table_id is None
                        or catalog is None
                        or schema is None
                        or table_name is None
                        or table_dialect is None
                    ):
                        raise DagsterInvariantViolationError(
                            f"Expected to find sdf table metadata on asset {asset_key.to_user_string()},"
                            " but did not. Did you pass in assets that weren't generated by @sdf_assets?"
                            " Please ensure that the asset metadata contains the following keys: "
                            f"{DAGSTER_SDF_TABLE_ID}, {DAGSTER_SDF_CATALOG_NAME}, {DAGSTER_SDF_SCHEMA_NAME}, {DAGSTER_SDF_TABLE_NAME}, {DAGSTER_SDF_DIALECT}"
                        )
                    run_args.append(table_id)
                    test_name_prefix = get_test_prefix(table_dialect)
                    # If the command is test, then we need to add the test name to the run_args (temporary: until sdf-cli applies --targets-only for test)
                    if args[0] == "test":
                        run_args.append(f"{catalog}.{schema}.{test_name_prefix}{table_name}")

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
            *run_args,
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

    def _validate_sdf_version(self) -> None:
        """Validate that the sdf version is compatible with the current version of the sdf CLI."""
        try:
            result = subprocess.run(
                ["sdf", "--version"], capture_output=True, text=True, check=True
            )
            output = result.stdout.strip()
            match = re.search(r"sdf (\d+\.\d+\.\d+)", output)
            if match:
                version = match.group(1)
                if version < SDF_VERSION_LOWER_BOUND or version >= SDF_VERSION_UPPER_BOUND:
                    logging.warn(
                        f"The sdf version '{version}' is not within the supported range of"
                        f" '{SDF_VERSION_LOWER_BOUND}' to '{SDF_VERSION_UPPER_BOUND}'. Check your"
                        " environment to ensure that the correct version of sdf is being used."
                    )
            else:
                logging.warn(
                    "Failed to extract the sdf version from the output. Check your environment to"
                    " ensure that the correct version of sdf is being used."
                )
        except subprocess.CalledProcessError as e:
            logging.warn(f"Failed to get the sdf version: {e}")
            exit(1)
