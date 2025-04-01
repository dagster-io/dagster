import contextlib
import copy
import os
import shutil
import signal
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, NamedTuple, Optional, Union, cast

import orjson
from dagster import (
    AssetCheckEvaluation,
    AssetCheckResult,
    AssetExecutionContext,
    AssetMaterialization,
    AssetObservation,
    OpExecutionContext,
    Output,
    get_dagster_logger,
)
from dagster._annotations import public
from dagster._core.errors import DagsterExecutionInterruptedError
from dbt.adapters.base.impl import BaseAdapter, BaseColumn, BaseRelation
from typing_extensions import Literal

from dagster_dbt.core.dbt_cli_event import DbtCliEventMessage
from dagster_dbt.core.dbt_event_iterator import DbtDagsterEventType, DbtEventIterator
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.errors import DagsterDbtCliRuntimeError

PARTIAL_PARSE_FILE_NAME = "partial_parse.msgpack"
DAGSTER_DBT_TERMINATION_TIMEOUT_SECONDS = int(
    os.getenv("DAGSTER_DBT_TERMINATION_TIMEOUT_SECONDS", "25")
)
DEFAULT_EVENT_POSTPROCESSING_THREADPOOL_SIZE: Final[int] = 4


logger = get_dagster_logger()


def _get_dbt_target_path() -> Path:
    return Path(os.getenv("DBT_TARGET_PATH", "target"))


class RelationKey(NamedTuple):
    """Hashable representation of the information needed to identify a relation in a database."""

    database: str
    schema: str
    identifier: str


class RelationData(NamedTuple):
    """Relation metadata queried from a database."""

    name: str
    columns: list[BaseColumn]


def _get_relation_from_adapter(adapter: BaseAdapter, relation_key: RelationKey) -> BaseRelation:
    return adapter.Relation.create(
        database=relation_key.database,
        schema=relation_key.schema,
        identifier=relation_key.identifier,
    )


@dataclass
class DbtCliInvocation:
    """The representation of an invoked dbt command.

    Args:
        process (subprocess.Popen): The process running the dbt command.
        manifest (Mapping[str, Any]): The dbt manifest blob.
        project_dir (Path): The path to the dbt project.
        target_path (Path): The path to the dbt target folder.
        raise_on_error (bool): Whether to raise an exception if the dbt command fails.
    """

    process: subprocess.Popen
    manifest: Mapping[str, Any]
    dagster_dbt_translator: DagsterDbtTranslator
    project_dir: Path
    target_path: Path
    raise_on_error: bool
    context: Optional[Union[OpExecutionContext, AssetExecutionContext]] = field(
        default=None, repr=False
    )
    termination_timeout_seconds: float = field(
        init=False, default=DAGSTER_DBT_TERMINATION_TIMEOUT_SECONDS
    )
    adapter: Optional[BaseAdapter] = field(default=None)
    postprocessing_threadpool_num_threads: int = field(
        init=False, default=DEFAULT_EVENT_POSTPROCESSING_THREADPOOL_SIZE
    )
    _stdout: list[Union[str, dict[str, Any]]] = field(init=False, default_factory=list)
    _error_messages: list[str] = field(init=False, default_factory=list)

    # Caches fetching relation column metadata to avoid redundant queries to the database.
    _relation_column_metadata_cache: dict[RelationKey, RelationData] = field(
        init=False, default_factory=dict
    )

    def _get_columns_from_dbt_resource_props(
        self, adapter: BaseAdapter, dbt_resource_props: dict[str, Any]
    ) -> RelationData:
        """Given a dbt resource properties dictionary, fetches the resource's column metadata from
        the database, or returns the cached metadata if it has already been fetched.
        """
        relation_key = RelationKey(
            database=dbt_resource_props["database"],
            schema=dbt_resource_props["schema"],
            identifier=(
                dbt_resource_props["identifier"]
                if dbt_resource_props["unique_id"].startswith("source")
                else dbt_resource_props["alias"]
            ),
        )
        if relation_key in self._relation_column_metadata_cache:
            return self._relation_column_metadata_cache[relation_key]

        relation = _get_relation_from_adapter(adapter=adapter, relation_key=relation_key)
        cols: list = adapter.get_columns_in_relation(relation=relation)
        return self._relation_column_metadata_cache.setdefault(
            relation_key, RelationData(name=str(relation), columns=cols)
        )

    @classmethod
    def run(
        cls,
        args: Sequence[str],
        env: dict[str, str],
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
        project_dir: Path,
        target_path: Path,
        raise_on_error: bool,
        context: Optional[Union[OpExecutionContext, AssetExecutionContext]],
        adapter: Optional[BaseAdapter],
    ) -> "DbtCliInvocation":
        # Attempt to take advantage of partial parsing. If there is a `partial_parse.msgpack` in
        # in the target folder, then copy it to the dynamic target path.
        #
        # This effectively allows us to skip the parsing of the manifest, which can be expensive.
        # See https://docs.getdbt.com/reference/programmatic-invocations#reusing-objects for more
        # details.
        current_target_path = _get_dbt_target_path()
        partial_parse_file_path = (
            current_target_path.joinpath(PARTIAL_PARSE_FILE_NAME)
            if current_target_path.is_absolute()
            else project_dir.joinpath(current_target_path, PARTIAL_PARSE_FILE_NAME)
        )
        partial_parse_destination_target_path = target_path.joinpath(PARTIAL_PARSE_FILE_NAME)

        if partial_parse_file_path.exists() and not partial_parse_destination_target_path.exists():
            logger.info(
                f"Copying `{partial_parse_file_path}` to `{partial_parse_destination_target_path}`"
                " to take advantage of partial parsing."
            )

            partial_parse_destination_target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(partial_parse_file_path, partial_parse_destination_target_path)

        # Create a subprocess that runs the dbt CLI command.
        process = subprocess.Popen(
            args=args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=project_dir,
        )

        dbt_cli_invocation = cls(
            process=process,
            manifest=manifest,
            dagster_dbt_translator=dagster_dbt_translator,
            project_dir=project_dir,
            target_path=target_path,
            raise_on_error=raise_on_error,
            context=context,
            adapter=adapter,
        )
        logger.info(f"Running dbt command: `{dbt_cli_invocation.dbt_command}`.")

        return dbt_cli_invocation

    @public
    def wait(self) -> "DbtCliInvocation":
        """Wait for the dbt CLI process to complete.

        Returns:
            DbtCliInvocation: The current representation of the dbt CLI invocation.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtCliResource

                dbt = DbtCliResource(project_dir="/path/to/dbt/project")

                dbt_cli_invocation = dbt.cli(["run"]).wait()
        """
        list(self.stream_raw_events())

        return self

    @public
    def is_successful(self) -> bool:
        """Return whether the dbt CLI process completed successfully.

        Returns:
            bool: True, if the dbt CLI process returns with a zero exit code, and False otherwise.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtCliResource

                dbt = DbtCliResource(project_dir="/path/to/dbt/project")

                dbt_cli_invocation = dbt.cli(["run"], raise_on_error=False)

                if dbt_cli_invocation.is_successful():
                    ...
        """
        self._stdout = list(self._stream_stdout())

        return self.process.wait() == 0 and not self._error_messages

    @public
    def get_error(self) -> Optional[Exception]:
        """Return an exception if the dbt CLI process failed.

        Returns:
            Optional[Exception]: An exception if the dbt CLI process failed, and None otherwise.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtCliResource

                dbt = DbtCliResource(project_dir="/path/to/dbt/project")

                dbt_cli_invocation = dbt.cli(["run"], raise_on_error=False)

                error = dbt_cli_invocation.get_error()
                if error:
                    logger.error(error)
        """
        if self.is_successful():
            return None

        log_path = self.target_path.joinpath("dbt.log")
        extra_description = ""

        if log_path.exists():
            extra_description = f", or view the dbt debug log: {log_path}"

        return DagsterDbtCliRuntimeError(
            description=(
                f"The dbt CLI process with command\n\n"
                f"`{self.dbt_command}`\n\n"
                f"failed with exit code `{self.process.returncode}`."
                " Check the stdout in the Dagster compute logs for the full information about"
                f" the error{extra_description}.{self._format_error_messages()}"
            ),
        )

    def _stream_asset_events(
        self,
    ) -> Iterator[DbtDagsterEventType]:
        """Stream the dbt CLI events and convert them to Dagster events."""
        for event in self.stream_raw_events():
            yield from event.to_default_asset_events(
                manifest=self.manifest,
                dagster_dbt_translator=self.dagster_dbt_translator,
                context=self.context,
                target_path=self.target_path,
            )

    @public
    def stream(
        self,
    ) -> "DbtEventIterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult, AssetCheckEvaluation]]":
        """Stream the events from the dbt CLI process and convert them to Dagster events.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult, AssetCheckEvaluation]]:
                A set of corresponding Dagster events.

                In a Dagster asset definition, the following are yielded:
                - Output for refables (e.g. models, seeds, snapshots.)
                - AssetCheckResult for dbt test results that are enabled as asset checks.
                - AssetObservation for dbt test results that are not enabled as asset checks.

                In a Dagster op definition, the following are yielded:
                - AssetMaterialization refables (e.g. models, seeds, snapshots.)
                - AssetCheckEvaluation for dbt test results that are enabled as asset checks.
                - AssetObservation for dbt test results that are not enabled as asset checks.

        Examples:
            .. code-block:: python

                from pathlib import Path
                from dagster_dbt import DbtCliResource, dbt_assets

                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context, dbt: DbtCliResource):
                    yield from dbt.cli(["run"], context=context).stream()
        """
        return DbtEventIterator(
            self._stream_asset_events(),
            self,
        )

    @public
    def stream_raw_events(self) -> Iterator[DbtCliEventMessage]:
        """Stream the events from the dbt CLI process.

        Returns:
            Iterator[DbtCliEventMessage]: An iterator of events from the dbt CLI process.
        """
        event_history_metadata_by_unique_id: dict[str, dict[str, Any]] = {}

        for raw_event in self._stdout or self._stream_stdout():
            if isinstance(raw_event, str):
                # If we can't parse the event, then just emit it as a raw log.
                sys.stdout.write(raw_event + "\n")
                sys.stdout.flush()

                continue

            unique_id: Optional[str] = raw_event["data"].get("node_info", {}).get("unique_id")
            is_result_event = DbtCliEventMessage.is_result_event(raw_event)
            event_history_metadata: dict[str, Any] = {}
            if unique_id and is_result_event:
                event_history_metadata = copy.deepcopy(
                    event_history_metadata_by_unique_id.get(unique_id, {})
                )

            event = DbtCliEventMessage(
                raw_event=raw_event, event_history_metadata=event_history_metadata
            )

            # Attempt to parse the column level metadata from the event message.
            # If it exists, save it as historical metadata to attach to the NodeFinished event.
            if event.raw_event["info"]["name"] == "JinjaLogInfo":
                with contextlib.suppress(orjson.JSONDecodeError):
                    column_level_metadata = orjson.loads(event.raw_event["info"]["msg"])

                    event_history_metadata_by_unique_id[cast(str, unique_id)] = (
                        column_level_metadata
                    )

                    # Don't show this message in stdout
                    continue

            # Re-emit the logs from dbt CLI process into stdout.
            sys.stdout.write(str(event) + "\n")
            sys.stdout.flush()

            yield event

        # Ensure that the dbt CLI process has completed.
        self._raise_on_error()

    @public
    def get_artifact(
        self,
        artifact: Union[
            Literal["manifest.json"],
            Literal["catalog.json"],
            Literal["run_results.json"],
            Literal["sources.json"],
        ],
    ) -> dict[str, Any]:
        """Retrieve a dbt artifact from the target path.

        See https://docs.getdbt.com/reference/artifacts/dbt-artifacts for more information.

        Args:
            artifact (Union[Literal["manifest.json"], Literal["catalog.json"], Literal["run_results.json"], Literal["sources.json"]]): The name of the artifact to retrieve.

        Returns:
            Dict[str, Any]: The artifact as a dictionary.

        Examples:
            .. code-block:: python

                from dagster_dbt import DbtCliResource

                dbt = DbtCliResource(project_dir="/path/to/dbt/project")

                dbt_cli_invocation = dbt.cli(["run"]).wait()

                # Retrieve the run_results.json artifact.
                run_results = dbt_cli_invocation.get_artifact("run_results.json")
        """
        artifact_path = self.target_path.joinpath(artifact)

        return orjson.loads(artifact_path.read_bytes())

    @property
    def dbt_command(self) -> str:
        """The dbt CLI command that was invoked."""
        return " ".join(cast(Sequence[str], self.process.args))

    def _stream_stdout(self) -> Iterator[Union[str, dict[str, Any]]]:
        """Stream the stdout from the dbt CLI process."""
        try:
            if not self.process.stdout or self.process.stdout.closed:
                return

            with self.process.stdout:
                for raw_line in self.process.stdout or []:
                    raw_event_str = raw_line.decode().strip()

                    try:
                        raw_event = orjson.loads(raw_event_str)

                        # Parse the error message from the event, if it exists.
                        is_error_message = raw_event["info"]["level"] == "error"
                        if is_error_message:
                            self._error_messages.append(raw_event["info"]["msg"])

                        yield raw_event
                    except:
                        yield raw_event_str

        except DagsterExecutionInterruptedError:
            logger.info(f"Forwarding interrupt signal to dbt command: `{self.dbt_command}`.")
            self.process.send_signal(signal.SIGINT)
            self.process.wait(timeout=self.termination_timeout_seconds)
            logger.info(f"dbt process terminated with exit code `{self.process.returncode}`.")

            raise

    def _format_error_messages(self) -> str:
        """Format the error messages from the dbt CLI process."""
        if not self._error_messages:
            return ""

        return "\n\n".join(
            [
                "",
                "Errors parsed from dbt logs:",
                *self._error_messages,
            ]
        )

    def _raise_on_error(self) -> None:
        """Ensure that the dbt CLI process has completed. If the process has not successfully
        completed, then optionally raise an error.
        """
        logger.info(f"Finished dbt command: `{self.dbt_command}`.")
        error = self.get_error()
        if error and self.raise_on_error:
            raise error
