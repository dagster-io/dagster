import os
import shutil
import signal
import subprocess
import sys
import uuid
from collections import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generic, Iterator, List, Optional, Sequence, Union, cast

import orjson
from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    ConfigurableResource,
    OpExecutionContext,
    Output,
    get_dagster_logger,
)
from dagster._annotations import public
from dagster._core.errors import DagsterExecutionInterruptedError
from pydantic import Field, validator
from typing_extensions import Literal, TypeVar

from .asset_utils import dagster_name_fn, default_asset_key_fn
from .constants import (
    DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
    SDF_DAGSTER_OUTPUT_DIR,
    SDF_EXECUTABLE,
    SDF_TARGET_DIR,
    SDF_WORKSPACE_YML,
)
from .errors import DagsterSdfCliRuntimeError

logger = get_dagster_logger()

DAGSTER_SDF_TERMINATION_TIMEOUT_SECONDS = 2


@dataclass
class SdfCliEventMessage:
    """The representation of an sdf CLI event.

    Args:
        raw_event (Dict[str, Any]): The raw event dictionary.
    """

    raw_event: Dict[str, Any]

    @property
    def is_result_event(self) -> bool:
        return (
            self.raw_event["ev"] == "cmd.do.derived"
            and self.raw_event["ev_type"] == "close"
            and bool(self.raw_event.get("status"))
        )

    @public
    def to_default_asset_events(
        self,
        context: Optional[OpExecutionContext] = None,
    ) -> Iterator[Union[Output, AssetMaterialization]]:
        """Convert an sdf CLI event to a set of corresponding Dagster events.

        Args:
            context (Optional[OpExecutionContext]): The execution context.

        Returns:
            Iterator[Union[Output, AssetMaterialization]]:
                A set of corresponding Dagster events.

                In a Dagster asset definition, the following are yielded:
                - Output for refables (e.g. models)

                In a Dagster op definition, the following are yielded:
                - AssetMaterialization for refables (e.g. models)
        """
        if not self.is_result_event:
            return

        is_success = self.raw_event["status"] == "succeeded"
        if not is_success:
            return

        table_id = self.raw_event["table"]
        default_metadata = {
            "table_id": table_id,
            "Execution Duration": self.raw_event["ev_dur_ms"] / 1000,
        }

        has_asset_def = bool(context and context.has_assets_def)
        event = (
            Output(
                value=None,
                output_name=dagster_name_fn(table_id),
                metadata=default_metadata,
            )
            if has_asset_def
            else AssetMaterialization(
                asset_key=default_asset_key_fn(table_id),
                metadata=default_metadata,
            )
        )

        yield event


SdfDagsterEventType = Union[Output, AssetMaterialization]


@dataclass
class SdfCliInvocation:
    """The representation of an invoked sdf command.

    Args:
        process (subprocess.Popen): The process running the sdf command.
        target_dir (Path): The path to the target directory.
        output_dir (Path): The path to the output directory.
        raise_on_error (bool): Whether to raise an exception if the sdf command fails.
    """

    process: subprocess.Popen
    target_dir: Path
    output_dir: Path
    raise_on_error: bool
    context: Optional[OpExecutionContext] = field(default=None, repr=False)
    termination_timeout_seconds: float = field(
        init=False, default=DAGSTER_SDF_TERMINATION_TIMEOUT_SECONDS
    )
    _stdout: List[str] = field(init=False, default_factory=list)

    @classmethod
    def run(
        cls,
        args: Sequence[str],
        env: Dict[str, str],
        workspace_dir: Path,
        target_dir: Path,
        output_dir: Path,
        raise_on_error: bool,
        context: Optional[OpExecutionContext],
    ) -> "SdfCliInvocation":
        # Create a subprocess that runs the sdf CLI command.
        process = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=workspace_dir,
        )

        sdf_cli_invocation = cls(
            process=process,
            target_dir=target_dir,
            output_dir=output_dir,
            raise_on_error=raise_on_error,
            context=context,
        )
        logger.info(f"Running sdf command: `{sdf_cli_invocation.sdf_command}`.")

        return sdf_cli_invocation

    @public
    def wait(self) -> "SdfCliInvocation":
        """Wait for the sdf CLI process to complete.

        Returns:
            SdfCliInvocation: The current representation of the sdf CLI invocation.
        """
        list(self.stream_raw_events())

        return self

    @public
    def is_successful(self) -> bool:
        """Return whether the sdf CLI process completed successfully.

        Returns:
            bool: True, if the sdf CLI process returns with a zero exit code, and False otherwise.
        """
        self._stdout = list(self._stream_stdout())

        return self.process.wait() == 0

    @public
    def get_error(self) -> Optional[Exception]:
        """Return an exception if the sdf CLI process failed.

        Returns:
            Optional[Exception]: An exception if the sdf CLI process failed, and None otherwise.
        """
        if self.is_successful():
            return None

        return DagsterSdfCliRuntimeError(
            description=(
                f"The sdf CLI process with command\n\n"
                f"`{self.sdf_command}`\n\n"
                f"failed with exit code `{self.process.returncode}`."
            ),
        )

    def _stream_asset_events(
        self,
    ) -> Iterator[SdfDagsterEventType]:
        """Stream the sdf CLI events and convert them to Dagster events."""
        for event in self.stream_raw_events():
            yield from event.to_default_asset_events(context=self.context)

    @public
    def stream(
        self,
    ) -> "SdfEventIterator[Union[Output, AssetMaterialization]]":
        """Stream the events from the sdf CLI process and convert them to Dagster events.

        Returns:
            Iterator[Union[Output, AssetMaterialization]]:
                A set of corresponding Dagster events.

                In a Dagster asset definition, the following are yielded:
                - Output for refables (e.g. models)

                In a Dagster op definition, the following are yielded:
                - AssetMaterialization for refables (e.g. models)

        Examples:
            .. code-block:: python

                from pathlib import Path
                from dagster_sdf import SdfCliResource, sdf_assets


                @sdf_assets(manifest=Path("target", "manifest.json"))
                def my_sdf_assets(context, sdf: SdfCliResource):
                    yield from sdf.cli(["run"], context=context).stream()
        """
        return SdfEventIterator(
            self._stream_asset_events(),
            self,
        )

    @public
    def stream_raw_events(self) -> Iterator[SdfCliEventMessage]:
        """Stream the events from the sdf CLI process.

        Returns:
            Iterator[SdfCliEventMessage]: An iterator of events from the sdf CLI process.
        """
        for log in self._stdout or self._stream_stdout():
            try:
                yield SdfCliEventMessage(raw_event=orjson.loads(log))
            except Exception:
                # If we can't parse the log, then just emit it as a raw log.
                sys.stdout.write(log + "\n")
                sys.stdout.flush()

        # Ensure that the sdf CLI process has completed.
        self._raise_on_error()

    @public
    def get_artifact(
        self,
        artifact: Union[
            Literal["makefile-compile.json"],
            Literal["makefile-run.json"],
        ],
    ) -> Dict[str, Any]:
        """Retrieve an sdf artifact from the target path.

        Args:
            artifact (Union[Literal["makefile-compile.json"], Literal["makefile-run.json"]]): The name of the artifact to retrieve.

        Returns:
            Dict[str, Any]: The artifact as a dictionary.

        Examples:
            .. code-block:: python

                from dagster_sdf import SdfCliResource

                sdf = SdfCliResource(workspace_dir="/path/to/sdf/workspace")

                sdf_cli_invocation = sdf.cli(["run"]).wait()

                # Retrieve the makefile-run.json artifact.
                run_results = sdf_cli_invocation.get_artifact("makefile-run.json")
        """
        artifact_path = self.output_dir.joinpath(artifact)

        return orjson.loads(artifact_path.read_bytes())

    @property
    def sdf_command(self) -> str:
        """The sdf CLI command that was invoked."""
        return " ".join(cast(Sequence[str], self.process.args))

    def _stream_stdout(self) -> Iterator[str]:
        """Stream the stdout from the sdf CLI process."""
        try:
            if not self.process.stdout or self.process.stdout.closed:
                return

            with self.process.stdout:
                for raw_line in self.process.stdout or []:
                    log: str = raw_line.decode().strip()

                    yield log
        except DagsterExecutionInterruptedError:
            logger.info(f"Forwarding interrupt signal to sdf command: `{self.sdf_command}`.")

            self.process.send_signal(signal.SIGINT)
            self.process.wait(timeout=self.termination_timeout_seconds)

            raise

    def _raise_on_error(self) -> None:
        """Ensure that the sdf CLI process has completed. If the process has not successfully
        completed, then optionally raise an error.
        """
        logger.info(f"Finished sdf command: `{self.sdf_command}`.")
        error = self.get_error()
        if error and self.raise_on_error:
            raise error


# We define SdfEventIterator as a generic type for the sake of type hinting.
# This is so that users who inspect the type of the return value of `SdfCliInvocation.stream()`
# will be able to see the inner type of the iterator, rather than just `SdfEventIterator`.
T = TypeVar("T", bound=SdfDagsterEventType)


class SdfEventIterator(Generic[T], abc.Iterator):
    """A wrapper around an iterator of sdf events which contains additional methods for
    post-processing the events.
    """

    def __init__(
        self,
        events: Iterator[T],
        sdf_cli_invocation: SdfCliInvocation,
    ) -> None:
        self._inner_iterator = events
        self._sdf_cli_invocation = sdf_cli_invocation

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "SdfEventIterator[T]":
        return self


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
        workspace_dir: Union[str, Path],
        global_config_flags: Optional[List[str]] = None,
        sdf_executable: str = SDF_EXECUTABLE,
        **kwargs,  # allow custom subclasses to add fields
    ):
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
        context = (
            context.op_execution_context if isinstance(context, AssetExecutionContext) else context
        )

        # Pass the current environment variables to the sdf CLI invocation.
        env = os.environ.copy()

        environment_args = ["--environment", environment]
        target_path = target_dir or self._get_unique_target_path(context=context)
        target_args = ["--target-dir", str(target_path)]
        log_level_args = ["--log-level", "info"]

        output_dir = target_path.joinpath(SDF_TARGET_DIR, environment)

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
            output_dir=output_dir,
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
