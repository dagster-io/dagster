import copy
import os
import signal
import subprocess
import sys
import uuid
from collections import abc
from dataclasses import InitVar, dataclass, field
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generic,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Union,
    cast,
)

import orjson
from dagster import (
    AssetCheckResult,
    AssetExecutionContext,
    AssetMaterialization,
    AssetObservation,
    ConfigurableResource,
    OpExecutionContext,
    Output,
    TimestampMetadataValue,
    get_dagster_logger,
)
from dagster._annotations import public
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._utils import pushd
from pydantic import Field
from typing_extensions import Final, TypeVar
from dateutil import parser

from .asset_utils import dagster_name_fn
from .sdf_workspace import SdfWorkspace
from .constants import DEFAULT_SDF_WORKSPACE_ENVIRONMENT, SDF_EXECUTABLE, SDF_DAGSTER_OUTPUT_DIR
from .errors import DagsterSdfCliRuntimeError
from .asset_utils import default_asset_key_fn


logger = get_dagster_logger()

DAGSTER_SDF_TERMINATION_TIMEOUT_SECONDS = 2
DEFAULT_EVENT_POSTPROCESSING_THREADPOOL_SIZE: Final[int] = 4

@dataclass
class SdfCliEventMessage:
    """The representation of an sdf CLI event.

    Args:
        raw_event (Dict[str, Any]): The raw event dictionary.
        event_history_metadata (Dict[str, Any]): A dictionary of metadata about the
            current event, gathered from previous historical events.
    """

    raw_event: Dict[str, Any]
    event_history_metadata: InitVar[Dict[str, Any]]

    def __post_init__(self, event_history_metadata: Dict[str, Any]):
        self._event_history_metadata = event_history_metadata

    def __str__(self) -> str:
        return str(self.raw_event)

    @staticmethod
    def is_result_event(raw_event: Dict[str, Any]) -> bool:
        return raw_event["ev"] == "cmd.do.derived" and raw_event["ev_type"] == "close"
    
    @staticmethod
    def is_error_event(raw_event: Dict[str, Any]) -> bool:
        return raw_event["ev"] == "cmd.do.derived" and raw_event["ev_type"] == "close" and raw_event["status"] == "failed"

    @public
    def to_default_asset_events(
        self,
        context: Optional[OpExecutionContext] = None,
    ) -> Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
        """Convert an sdf CLI event to a set of corresponding Dagster events.

        Args:
            context (Optional[OpExecutionContext]): The execution context.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
                A set of corresponding Dagster events.

                In a Dagster asset definition, the following are yielded:
                - Output for refables (e.g. models)
                - AssetCheckResult for sdf test results that are enabled as asset checks.
                - AssetObservation for sdf test results that are not enabled as asset checks.

                In a Dagster op definition, the following are yielded:
                - AssetMaterialization for sdf test results that are not enabled as asset checks.
                - AssetObservation for sdf test results.
        """
        if not self.is_result_event(self.raw_event):
            return
        
        is_success: bool = self.raw_event["status"] == "succeeded"

        table_id: str = self.raw_event["table"]
        timestamp_str: str = self.raw_event["__ts"]
        try:
            dt = parser.parse(timestamp_str)
            float_timestamp = dt.timestamp()
            materialized_at = TimestampMetadataValue(float_timestamp)
        except:
            materialized_at = timestamp_str

        default_metadata = {
            "table_id": table_id,
            "materialized_at": materialized_at,
            "Execution Duration": self.raw_event["ev_dur_ms"] / 1000,
        }

        has_asset_def: bool = bool(context and context.has_assets_def)

        if is_success:
            if has_asset_def:
                yield Output(
                    value=None,
                    output_name=dagster_name_fn(table_id),
                    metadata={
                        **default_metadata,
                    },
                )
            else:
                yield AssetMaterialization(
                    asset_key=default_asset_key_fn(table_id),
                    metadata={
                        **default_metadata,
                    },
                )

SdfDagsterEventType = Union[Output, AssetMaterialization, AssetCheckResult, AssetObservation]

@dataclass
class SdfCliInvocation:
    """The representation of an invoked sdf command.

    Args:
        process (subprocess.Popen): The process running the sdf command.
        information_schema (SdfInformationSchema): The information schema for sdf nodes.
        dagster_sdf_translator (DagsterSdfTranslator): The translator for sdf nodes to Dagster assets.
        workspace_dir (Path): The path to the sdf workspace.
        target_dir (Path): The path to the target directory.
        output_dir (Path): The path to the output directory.
        raise_on_error (bool): Whether to raise an exception if the sdf command fails.
    """

    process: subprocess.Popen
    workspace_dir: Path
    target_dir: Path
    output_dir: Path
    raise_on_error: bool
    context: Optional[OpExecutionContext] = field(default=None, repr=False)
    termination_timeout_seconds: float = field(
        init=False, default=DAGSTER_SDF_TERMINATION_TIMEOUT_SECONDS
    )
    postprocessing_threadpool_num_threads: int = field(
        init=False, default=DEFAULT_EVENT_POSTPROCESSING_THREADPOOL_SIZE
    )
    _stdout: List[str] = field(init=False, default_factory=list)
    _error_messages: List[str] = field(init=False, default_factory=list)

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
            workspace_dir=workspace_dir,
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

        log_path = self.output_dir.joinpath("sdf_dagster.log")
        extra_description = ""

        if log_path.exists():
            extra_description = f", or view the sdf debug log: {log_path}"

        return DagsterSdfCliRuntimeError(
            description=(
                f"The sdf CLI process with command\n\n"
                f"`{self.sdf_command}`\n\n"
                f"failed with exit code `{self.process.returncode}`."
                " Check the stdout in the Dagster compute logs for the full information about"
                f" the error{extra_description}.{self._format_error_messages()}"
            ),
        )

    def _stream_asset_events(
        self,
    ) -> Iterator[SdfDagsterEventType]:
        """Stream the sdf CLI events and convert them to Dagster events."""
        for event in self.stream_raw_events():
            yield from event.to_default_asset_events(
                context=self.context
            )

    @public
    def stream(
        self,
    ) -> (
        "SdfEventIterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]"
    ):
        """Stream the events from the sdf CLI process and convert them to Dagster events.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
                A set of corresponding Dagster events.

                In a Dagster asset definition, the following are yielded:
                - Output for refables (e.g. models, seeds, snapshots.)
                - AssetCheckResult for sdf test results that are enabled as asset checks.
                - AssetObservation for sdf test results that are not enabled as asset checks.

                In a Dagster op definition, the following are yielded:
                - AssetMaterialization for sdf test results that are not enabled as asset checks.
                - AssetObservation for sdf test results.

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
        event_history_metadata_by_unique_id: Dict[str, Dict[str, Any]] = {}

        for log in self._stdout or self._stream_stdout():
            try:
                raw_event: Dict[str, Any] = orjson.loads(log)
                unique_id: Optional[str] = raw_event["table"]
                is_result_event = SdfCliEventMessage.is_result_event(raw_event)
                event_history_metadata: Dict[str, Any] = {}
                if unique_id and is_result_event:
                    event_history_metadata = copy.deepcopy(
                        event_history_metadata_by_unique_id.get(unique_id, {})
                    )

                event = SdfCliEventMessage(
                    raw_event=raw_event, event_history_metadata=event_history_metadata
                )
                print("EVENT", event)
                # Parse the error message from the event, if it exists.
                is_error_message = SdfCliEventMessage.is_error_event(raw_event)
                if is_error_message and not is_result_event:
                    self._error_messages.append(str(event))
                    
                # Re-emit the logs from sdf CLI process into stdout.
                sys.stdout.write(str(event) + "\n")
                sys.stdout.flush()
                yield event
            except Exception as e:
                print("FAILED TO PARSE", e)
                # If we can't parse the log, then just emit it as a raw log.
                sys.stdout.write(log + "\n")
                sys.stdout.flush()

        # Ensure that the sdf CLI process has completed.
        self._raise_on_error()

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

    def _format_error_messages(self) -> str:
        """Format the error messages from the sdf CLI process."""
        if not self._error_messages:
            return ""

        return "\n\n".join(
            [
                "",
                "Errors parsed from sdf logs:",
                *self._error_messages,
            ]
        )

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

class EventHistoryMetadata(NamedTuple):
    columns: Dict[str, Dict[str, Any]]
    parents: Dict[str, Dict[str, Any]]


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
        description=(
            "A list of global flags configuration to pass to the sdf CLI"
            " invocation."
        ),
    )   
    sdf_executable: str = Field(
        default=SDF_EXECUTABLE,
        description="The path to the sdf executable.",
    )

    def __init__(
        self,
        workspace_dir: Union[str, SdfWorkspace],
        global_config_flags: Optional[List[str]] = None,
        sdf_executable: str = SDF_EXECUTABLE,
        **kwargs,  # allow custom subclasses to add fields
    ):
        if isinstance(workspace_dir, SdfWorkspace):
            workspace_dir = os.fspath(workspace_dir.workspace_dir)
        # static typing doesn't understand whats going on here, thinks these fields dont exist
        super().__init__(
            workspace_dir=workspace_dir,  # type: ignore
            global_config_flags=global_config_flags or [],  # type: ignore
            sdf_executable=sdf_executable,  # type: ignore
            **kwargs,
        )

    @public
    def cli(
        self,
        args: Sequence[str],
        *,
        target_dir: Optional[str] = None,
        environment: Optional[str] = None,
        raise_on_error: bool = True,
        context: Optional[Union[OpExecutionContext, AssetExecutionContext]] = None,
    ) -> SdfCliInvocation:
        """Create a subprocess to execute an sdf CLI command.

        Args:
            args (Sequence[str]): The sdf CLI command to execute.
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
        if target_dir:
            unique_target_path = Path(target_dir)
        else:
            unique_target_path = self._get_unique_target_path(context=context)
        env = {
            # Pass the current environment variables to the sdf CLI invocation.
            **os.environ.copy()
        }
        # TODO: verify that args does not have any selection flags if the context and manifest
        # are passed to this function.
        environment = environment or DEFAULT_SDF_WORKSPACE_ENVIRONMENT
        environment_args: List[str] = ["--environment", environment]
        target_args: List[str] = ["--target-dir", str(unique_target_path)]

        output_dir = unique_target_path.joinpath(environment)

        # Ensure that the target_dir exists
        unique_target_path.mkdir(parents=True, exist_ok=True)

        args = [
            self.sdf_executable,
            *args,
            *self.global_config_flags,
            *environment_args,
            *target_args,
        ]
        workspace_dir = Path(self.workspace_dir)

        with pushd(self.workspace_dir):
            return SdfCliInvocation.run(
                args=args,
                env=env,
                workspace_dir=workspace_dir,
                target_dir=unique_target_path,
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