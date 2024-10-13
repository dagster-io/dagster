import os
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union, cast

import orjson
from dagster import OpExecutionContext, get_dagster_logger
from dagster._annotations import public
from dagster._core.errors import DagsterExecutionInterruptedError
from typing_extensions import Literal

from dagster_sdf.constants import SDF_TARGET_DIR
from dagster_sdf.dagster_sdf_translator import DagsterSdfTranslator
from dagster_sdf.errors import DagsterSdfCliRuntimeError
from dagster_sdf.sdf_cli_event import SdfCliEventMessage
from dagster_sdf.sdf_event_iterator import SdfDagsterEventType, SdfEventIterator
from dagster_sdf.sdf_information_schema import SdfInformationSchema

logger = get_dagster_logger()

DAGSTER_SDF_TERMINATION_TIMEOUT_SECONDS = int(
    os.getenv("DAGSTER_SDF_TERMINATION_TIMEOUT_SECONDS", "25")
)


@dataclass
class SdfCliInvocation:
    """The representation of an invoked sdf command.

    Args:
        process (subprocess.Popen): The process running the sdf command.
        workspace_dir (Path): The path to the workspace directory.
        target_dir (Path): The path to the target directory.
        enviornment (str): The environment to use.
        raise_on_error (bool): Whether to raise an exception if the sdf command fails.
    """

    process: subprocess.Popen
    workspace_dir: Path
    target_dir: Path
    environment: str
    dagster_sdf_translator: DagsterSdfTranslator
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
        environment: str,
        dagster_sdf_translator: DagsterSdfTranslator,
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
            environment=environment,
            dagster_sdf_translator=dagster_sdf_translator,
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
            yield from event.to_default_asset_events(
                dagster_sdf_translator=self.dagster_sdf_translator, context=self.context
            )
        yield from SdfInformationSchema(
            workspace_dir=self.workspace_dir,
            target_dir=self.target_dir,
            environment=self.environment,
        ).stream_asset_observations(
            dagster_sdf_translator=self.dagster_sdf_translator, context=self.context
        )

    @public
    def stream(
        self,
    ) -> "SdfEventIterator[SdfDagsterEventType]":
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


                @sdf_assets(workspace=SdfWorkspace(workspace_dir="/path/to/sdf/workspace"))
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
        artifact_path = self.target_dir.joinpath(SDF_TARGET_DIR, self.environment, artifact)

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

            logger.info(f"sdf process terminated with exit code `{self.process.returncode}`.")

            raise

    def _raise_on_error(self) -> None:
        """Ensure that the sdf CLI process has completed. If the process has not successfully
        completed, then optionally raise an error.
        """
        logger.info(f"Finished sdf command: `{self.sdf_command}`.")
        error = self.get_error()
        if error and self.raise_on_error:
            raise error
