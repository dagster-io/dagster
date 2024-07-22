import contextlib
import copy
import os
import shutil
import signal
import subprocess
import sys
from collections import abc
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Union,
    cast,
)

import orjson
from dagster import (
    AssetCheckResult,
    AssetMaterialization,
    AssetObservation,
    OpExecutionContext,
    Output,
    _check as check,
    get_dagster_logger,
)
from dagster._annotations import experimental, public
from dagster._core.definitions.metadata import TableMetadataSet, TextMetadataValue
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterInvalidPropertyError
from dbt.adapters.base.impl import BaseAdapter, BaseColumn, BaseRelation
from typing_extensions import Final, Literal, TypeVar

from ..asset_utils import default_metadata_from_dbt_resource_props
from ..dagster_dbt_translator import DagsterDbtTranslator
from ..errors import DagsterDbtCliRuntimeError
from .dbt_cli_event import DbtCliEventMessage, EventHistoryMetadata, _build_column_lineage_metadata
from .utils import exhaust_iterator_and_yield_results_with_exception, imap

PARTIAL_PARSE_FILE_NAME = "partial_parse.msgpack"
DAGSTER_DBT_TERMINATION_TIMEOUT_SECONDS = 2
DEFAULT_EVENT_POSTPROCESSING_THREADPOOL_SIZE: Final[int] = 4


logger = get_dagster_logger()


def _get_dbt_target_path() -> Path:
    return Path(os.getenv("DBT_TARGET_PATH", "target"))


DbtDagsterEventType = Union[Output, AssetMaterialization, AssetCheckResult, AssetObservation]


class RelationKey(NamedTuple):
    """Hashable representation of the information needed to identify a relation in a database."""

    database: str
    schema: str
    identifier: str


class RelationData(NamedTuple):
    """Relation metadata queried from a database."""

    name: str
    columns: List[BaseColumn]


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
    context: Optional[OpExecutionContext] = field(default=None, repr=False)
    termination_timeout_seconds: float = field(
        init=False, default=DAGSTER_DBT_TERMINATION_TIMEOUT_SECONDS
    )
    adapter: Optional[BaseAdapter] = field(default=None)
    postprocessing_threadpool_num_threads: int = field(
        init=False, default=DEFAULT_EVENT_POSTPROCESSING_THREADPOOL_SIZE
    )
    _stdout: List[Union[str, Dict[str, Any]]] = field(init=False, default_factory=list)
    _error_messages: List[str] = field(init=False, default_factory=list)

    # Caches fetching relation column metadata to avoid redundant queries to the database.
    _relation_column_metadata_cache: Dict[RelationKey, RelationData] = field(
        init=False, default_factory=dict
    )

    def _get_columns_from_dbt_resource_props(
        self, adapter: BaseAdapter, dbt_resource_props: Dict[str, Any]
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
        cols: List = adapter.get_columns_in_relation(relation=relation)
        return self._relation_column_metadata_cache.setdefault(
            relation_key, RelationData(name=str(relation), columns=cols)
        )

    @classmethod
    def run(
        cls,
        args: Sequence[str],
        env: Dict[str, str],
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
        project_dir: Path,
        target_path: Path,
        raise_on_error: bool,
        context: Optional[OpExecutionContext],
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
    ) -> (
        "DbtEventIterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]"
    ):
        """Stream the events from the dbt CLI process and convert them to Dagster events.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
                A set of corresponding Dagster events.

                In a Dagster asset definition, the following are yielded:
                - Output for refables (e.g. models, seeds, snapshots.)
                - AssetCheckResult for dbt test results that are enabled as asset checks.
                - AssetObservation for dbt test results that are not enabled as asset checks.

                In a Dagster op definition, the following are yielded:
                - AssetMaterialization for dbt test results that are not enabled as asset checks.
                - AssetObservation for dbt test results.

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
        event_history_metadata_by_unique_id: Dict[str, Dict[str, Any]] = {}

        for raw_event in self._stdout or self._stream_stdout():
            if isinstance(raw_event, str):
                # If we can't parse the event, then just emit it as a raw log.
                sys.stdout.write(raw_event + "\n")
                sys.stdout.flush()

                continue

            unique_id: Optional[str] = raw_event["data"].get("node_info", {}).get("unique_id")
            is_result_event = DbtCliEventMessage.is_result_event(raw_event)
            event_history_metadata: Dict[str, Any] = {}
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
    ) -> Dict[str, Any]:
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

    def _stream_stdout(self) -> Iterator[Union[str, Dict[str, Any]]]:
        """Stream the stdout from the dbt CLI process."""
        try:
            if not self.process.stdout or self.process.stdout.closed:
                return

            with self.process.stdout:
                for raw_line in self.process.stdout or []:
                    raw_event = raw_line.decode().strip()

                    try:
                        raw_event = orjson.loads(raw_event)

                        # Parse the error message from the event, if it exists.
                        is_error_message = raw_event["info"]["level"] == "error"
                        if is_error_message:
                            self._error_messages.append(raw_event["info"]["msg"])
                    except:
                        pass

                    yield raw_event
        except DagsterExecutionInterruptedError:
            logger.info(f"Forwarding interrupt signal to dbt command: `{self.dbt_command}`.")

            self.process.send_signal(signal.SIGINT)
            self.process.wait(timeout=self.termination_timeout_seconds)

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


# We define DbtEventIterator as a generic type for the sake of type hinting.
# This is so that users who inspect the type of the return value of `DbtCliInvocation.stream()`
# will be able to see the inner type of the iterator, rather than just `DbtEventIterator`.
T = TypeVar("T", bound=DbtDagsterEventType)


def _get_dbt_resource_props_from_event(
    invocation: DbtCliInvocation, event: DbtDagsterEventType
) -> Dict[str, Any]:
    unique_id = cast(TextMetadataValue, event.metadata["unique_id"]).text
    return check.not_none(invocation.manifest["nodes"].get(unique_id))


def _get_relation_from_adapter(adapter: BaseAdapter, relation_key: RelationKey) -> BaseRelation:
    return adapter.Relation.create(
        database=relation_key.database,
        schema=relation_key.schema,
        identifier=relation_key.identifier,
    )


def _fetch_column_metadata(
    invocation: DbtCliInvocation, event: DbtDagsterEventType, with_column_lineage: bool
) -> Optional[Dict[str, Any]]:
    """Threaded task which fetches column schema and lineage metadata for dbt models in a dbt
    run once they are built, returning the metadata to be attached.

    First we use the dbt adapter to obtain the column metadata for the built model. Then we
    retrieve the column metadata for the model's parent models, if they exist. Finally, we
    build the column lineage metadata for the model and attach it to the event.

    Args:
        invocation (DbtCliInvocation): The dbt CLI invocation.
        event (DbtDagsterEventType): The dbt event to append column metadata to.
        with_column_lineage (bool): Whether to include column lineage metadata in the event.
    """
    adapter = check.not_none(invocation.adapter)

    dbt_resource_props = _get_dbt_resource_props_from_event(invocation, event)

    with adapter.connection_named(f"column_metadata_{dbt_resource_props['unique_id']}"):
        try:
            cols = invocation._get_columns_from_dbt_resource_props(  # noqa: SLF001
                adapter=adapter, dbt_resource_props=dbt_resource_props
            ).columns
        except Exception as e:
            logger.warning(
                "An error occurred while fetching column schema metadata for the dbt resource"
                f" `{dbt_resource_props['original_file_path']}`."
                " Column metadata will not be included in the event.\n\n"
                f"Exception: {e}",
                exc_info=True,
            )
            return {}

        schema_metadata = {}
        try:
            column_schema_data = {col.name: {"data_type": col.data_type} for col in cols}
            col_data = {"columns": column_schema_data}
            schema_metadata = default_metadata_from_dbt_resource_props(col_data)
        except Exception as e:
            logger.warning(
                "An error occurred while building column schema metadata from data"
                f" `{col_data}` for the dbt resource"
                f" `{dbt_resource_props['original_file_path']}`."
                " Column schema metadata will not be included in the event.\n\n"
                f"Exception: {e}",
                exc_info=True,
            )

        lineage_metadata = {}
        if with_column_lineage:
            try:
                parents = {}
                parent_unique_ids = invocation.manifest["parent_map"].get(
                    dbt_resource_props["unique_id"], []
                )
                for parent_unique_id in parent_unique_ids:
                    dbt_parent_resource_props = invocation.manifest["nodes"].get(
                        parent_unique_id
                    ) or invocation.manifest["sources"].get(parent_unique_id)

                    parent_name, parent_columns = invocation._get_columns_from_dbt_resource_props(  # noqa: SLF001
                        adapter=adapter, dbt_resource_props=dbt_parent_resource_props
                    )

                    parents[parent_name] = {
                        col.name: {"data_type": col.data_type} for col in parent_columns
                    }

                lineage_metadata = _build_column_lineage_metadata(
                    event_history_metadata=EventHistoryMetadata(
                        columns=column_schema_data,
                        parents=parents,
                    ),
                    dbt_resource_props=dbt_resource_props,
                    manifest=invocation.manifest,
                    dagster_dbt_translator=invocation.dagster_dbt_translator,
                    target_path=invocation.target_path,
                )

            except Exception as e:
                logger.warning(
                    "An error occurred while building column lineage metadata for the dbt resource"
                    f" `{dbt_resource_props['original_file_path']}`."
                    " Lineage metadata will not be included in the event.\n\n"
                    f"Exception: {e}",
                    exc_info=True,
                )

        return {
            **schema_metadata,
            **lineage_metadata,
        }


def _fetch_row_count_metadata(
    invocation: DbtCliInvocation,
    event: DbtDagsterEventType,
) -> Optional[Dict[str, Any]]:
    """Threaded task which fetches row counts for materialized dbt models in a dbt run
    once they are built, and attaches the row count as metadata to the event.
    """
    if not isinstance(event, (AssetMaterialization, Output)):
        return None

    adapter = check.not_none(invocation.adapter)

    dbt_resource_props = _get_dbt_resource_props_from_event(invocation, event)
    is_view = dbt_resource_props["config"]["materialized"] == "view"

    # Avoid counting rows for views, since they may include complex SQL queries
    # that are costly to execute. We can revisit this in the future if there is
    # a demand for it.
    if is_view:
        return None

    unique_id = dbt_resource_props["unique_id"]
    logger.debug("Fetching row count for %s", unique_id)
    relation_name = dbt_resource_props["relation_name"]

    try:
        with adapter.connection_named(f"row_count_{unique_id}"):
            query_result = adapter.execute(
                f"""
                    SELECT
                    count(*) as row_count
                    FROM
                    {relation_name}
                """,
                fetch=True,
            )
        query_result_table = query_result[1]
        # some adapters do not output the column names, so we need
        # to index by position
        row_count = query_result_table[0][0]
        return {**TableMetadataSet(row_count=row_count)}

    except Exception as e:
        logger.exception(
            f"An error occurred while fetching row count for {unique_id}. Row count metadata"
            " will not be included in the event.\n\n"
            f"Exception: {e}"
        )
        return None


class DbtEventIterator(Generic[T], abc.Iterator):
    """A wrapper around an iterator of dbt events which contains additional methods for
    post-processing the events, such as fetching row counts for materialized tables.
    """

    def __init__(
        self,
        events: Iterator[T],
        dbt_cli_invocation: DbtCliInvocation,
    ) -> None:
        self._inner_iterator = events
        self._dbt_cli_invocation = dbt_cli_invocation

    def __next__(self) -> T:
        return next(self._inner_iterator)

    def __iter__(self) -> "DbtEventIterator[T]":
        return self

    @public
    @experimental
    def fetch_row_counts(
        self,
    ) -> (
        "DbtEventIterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]"
    ):
        """Experimental functionality which will fetch row counts for materialized dbt
        models in a dbt run once they are built. Note that row counts will not be fetched
        for views, since this requires running the view's SQL query which may be costly.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
                A set of corresponding Dagster events for dbt models, with row counts attached,
                yielded in the order they are emitted by dbt.
        """
        return self._attach_metadata(_fetch_row_count_metadata)

    @public
    @experimental
    def fetch_column_metadata(
        self,
        with_column_lineage: bool = True,
    ) -> (
        "DbtEventIterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]"
    ):
        """Experimental functionality which will fetch column schema metadata for dbt models in a run
        once they're built. It will also fetch schema information for upstream models and generate
        column lineage metadata using sqlglot, if enabled.

        Args:
            generate_column_lineage (bool): Whether to generate column lineage metadata using sqlglot.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
                A set of corresponding Dagster events for dbt models, with column metadata attached,
                yielded in the order they are emitted by dbt.
        """
        fetch_metadata = lambda invocation, event: _fetch_column_metadata(
            invocation, event, with_column_lineage
        )
        return self._attach_metadata(fetch_metadata)

    def _attach_metadata(
        self,
        fn: Callable[[DbtCliInvocation, DbtDagsterEventType], Optional[Dict[str, Any]]],
    ) -> "DbtEventIterator[DbtDagsterEventType]":
        """Runs a threaded task to attach metadata to each event in the iterator.

        Args:
            fn (Callable[[DbtCliInvocation, DbtDagsterEventType], Optional[Dict[str, Any]]]):
                A function which takes a DbtCliInvocation and a DbtDagsterEventType and returns
                a dictionary of metadata to attach to the event.

        Returns:
             Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
                A set of corresponding Dagster events for dbt models, with any metadata output
                by the function attached, yielded in the order they are emitted by dbt.
        """

        def _map_fn(event: DbtDagsterEventType) -> DbtDagsterEventType:
            result = fn(self._dbt_cli_invocation, event)
            if result is None:
                return event

            return event.with_metadata({**event.metadata, **result})

        # If the adapter is DuckDB, we need to wait for the dbt CLI process to complete
        # so that the DuckDB lock is released. This is because DuckDB does not allow for
        # opening multiple connections to the same database when a write connection, such
        # as the one dbt uses, is open.
        event_stream = self
        try:
            from dbt.adapters.duckdb import DuckDBAdapter

            if isinstance(self._dbt_cli_invocation.adapter, DuckDBAdapter):
                event_stream = exhaust_iterator_and_yield_results_with_exception(self)

        except ImportError:
            pass

        def _threadpool_wrap_map_fn() -> (
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]
        ):
            with ThreadPoolExecutor(
                max_workers=self._dbt_cli_invocation.postprocessing_threadpool_num_threads,
                thread_name_prefix=f"dbt_attach_metadata_{fn.__name__}",
            ) as executor:
                yield from imap(
                    executor=executor,
                    iterable=event_stream,
                    func=_map_fn,
                )

        return DbtEventIterator(
            _threadpool_wrap_map_fn(),
            dbt_cli_invocation=self._dbt_cli_invocation,
        )

    @public
    @experimental
    def with_insights(
        self,
        skip_config_check: bool = False,
        record_observation_usage: bool = True,
    ) -> (
        "DbtEventIterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]"
    ):
        """Associate each warehouse query with the produced asset materializations for use in Dagster
        Plus Insights. Currently supports Snowflake and BigQuery.

        For more information, see the documentation for
        `dagster_cloud.dagster_insights.dbt_with_snowflake_insights` and
        `dagster_cloud.dagster_insights.dbt_with_bigquery_insights`.

        Args:
            skip_config_check (bool): If true, skips the check that the dbt project config is set up
                correctly. Defaults to False.
            record_observation_usage (bool): If True, associates the usage associated with
                asset observations with that asset. Default is True.

        **Example:**

        .. code-block:: python

            @dbt_assets(manifest=DBT_MANIFEST_PATH)
            def jaffle_shop_dbt_assets(
                context: AssetExecutionContext,
                dbt: DbtCliResource,
            ):
                yield from dbt.cli(["build"], context=context).stream().with_insights()
        """
        adapter_type = self._dbt_cli_invocation.manifest.get("metadata", {}).get("adapter_type")
        if adapter_type == "snowflake":
            try:
                from dagster_cloud.dagster_insights import (  # pyright: ignore[reportMissingImports]
                    dbt_with_snowflake_insights,
                )
            except ImportError as e:
                raise DagsterInvalidPropertyError(
                    "The `dagster_cloud` library is required to use the `with_insights`"
                    " method. Install the library with `pip install dagster-cloud`."
                ) from e

            return DbtEventIterator(
                events=dbt_with_snowflake_insights(
                    context=self._dbt_cli_invocation.context,
                    dbt_cli_invocation=self._dbt_cli_invocation,
                    dagster_events=self,
                    skip_config_check=skip_config_check,
                    record_observation_usage=record_observation_usage,
                ),
                dbt_cli_invocation=self._dbt_cli_invocation,
            )
        elif adapter_type == "bigquery":
            try:
                from dagster_cloud.dagster_insights import (  # pyright: ignore[reportMissingImports]
                    dbt_with_bigquery_insights,
                )
            except ImportError as e:
                raise DagsterInvalidPropertyError(
                    "The `dagster_cloud` library is required to use the `with_insights`"
                    " method. Install the library with `pip install dagster-cloud`."
                ) from e

            return DbtEventIterator(
                events=dbt_with_bigquery_insights(
                    context=self._dbt_cli_invocation.context,
                    dbt_cli_invocation=self._dbt_cli_invocation,
                    dagster_events=self,
                    skip_config_check=skip_config_check,
                    record_observation_usage=record_observation_usage,
                ),
                dbt_cli_invocation=self._dbt_cli_invocation,
            )
        else:
            check.failed(
                f"The `with_insights` method is only supported for Snowflake and BigQuery and is not supported for adapter type `{adapter_type}`"
            )
