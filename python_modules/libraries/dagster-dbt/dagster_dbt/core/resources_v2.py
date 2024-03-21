import contextlib
import copy
import os
import shutil
import signal
import subprocess
import sys
import uuid
from contextlib import suppress
from dataclasses import InitVar, dataclass, field
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

import dateutil.parser
import orjson
from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetExecutionContext,
    AssetMaterialization,
    AssetObservation,
    AssetsDefinition,
    ConfigurableResource,
    OpExecutionContext,
    Output,
    get_dagster_logger,
)
from dagster._annotations import public
from dagster._config.pythonic_config.pydantic_compat_layer import compat_model_validator
from dagster._core.definitions.metadata import TableMetadataEntries
from dagster._core.definitions.metadata.table import TableColumnDep, TableColumnLineage
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterInvalidPropertyError
from dbt.contracts.results import NodeStatus, TestStatus
from dbt.node_types import NodeType
from dbt.version import __version__ as dbt_version
from packaging import version
from pydantic import Field, validator
from sqlglot import (
    MappingSchema,
    exp,
    parse_one,
)
from sqlglot.lineage import lineage
from sqlglot.optimizer import optimize
from typing_extensions import Literal

from ..asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
    dagster_name_fn,
    default_metadata_from_dbt_resource_props,
    get_manifest_and_translator_from_dbt_assets,
)
from ..dagster_dbt_translator import (
    DagsterDbtTranslator,
    validate_opt_translator,
    validate_translator,
)
from ..dbt_manifest import (
    DbtManifestParam,
    validate_manifest,
)
from ..errors import DagsterDbtCliRuntimeError
from ..utils import ASSET_RESOURCE_TYPES, get_dbt_resource_props_by_dbt_unique_id_from_manifest

logger = get_dagster_logger()


DBT_EXECUTABLE = "dbt"
DBT_PROJECT_YML_NAME = "dbt_project.yml"
DBT_PROFILES_YML_NAME = "profiles.yml"
PARTIAL_PARSE_FILE_NAME = "partial_parse.msgpack"
DAGSTER_DBT_TERMINATION_TIMEOUT_SECONDS = 2


def _get_dbt_target_path() -> Path:
    return Path(os.getenv("DBT_TARGET_PATH", "target"))


@dataclass
class DbtCliEventMessage:
    """The representation of a dbt CLI event.

    Args:
        raw_event (Dict[str, Any]): The raw event dictionary.
            See https://docs.getdbt.com/reference/events-logging#structured-logging for more
            information.
        event_history_metadata (Dict[str, Any]): A dictionary of metadata about the
            current event, gathered from previous historical events.
    """

    raw_event: Dict[str, Any]
    event_history_metadata: InitVar[Dict[str, Any]]

    def __post_init__(self, event_history_metadata: Dict[str, Any]):
        self._event_history_metadata = event_history_metadata

    def __str__(self) -> str:
        return self.raw_event["info"]["msg"]

    @property
    def log_level(self) -> str:
        """The log level of the event."""
        return self.raw_event["info"]["level"]

    @property
    def has_column_lineage_metadata(self) -> bool:
        """Whether the event has column level lineage metadata."""
        return bool(self._event_history_metadata) and "parents" in self._event_history_metadata

    @public
    def to_default_asset_events(
        self,
        manifest: DbtManifestParam,
        dagster_dbt_translator: DagsterDbtTranslator = DagsterDbtTranslator(),
        context: Optional[OpExecutionContext] = None,
        target_path: Optional[Path] = None,
    ) -> Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult]]:
        """Convert a dbt CLI event to a set of corresponding Dagster events.

        Args:
            manifest (Union[Mapping[str, Any], str, Path]): The dbt manifest blob.
            dagster_dbt_translator (DagsterDbtTranslator): Optionally, a custom translator for
                linking dbt nodes to Dagster assets.
            context (Optional[OpExecutionContext]): The execution context.
            target_path (Optional[Path]): An explicit path to a target folder used to retrieve
                dbt artifacts while generating events.

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

        """
        if self.raw_event["info"]["name"] != "NodeFinished":
            return

        adapter_response = self.raw_event["data"].get("run_result", {}).get("adapter_response", {})
        adapter_response_metadata = self._process_adapter_response_metadata(adapter_response)
        event_node_info: Dict[str, Any] = self.raw_event["data"].get("node_info")
        if not event_node_info or event_node_info["resource_type"] == "source":
            return

        dagster_dbt_translator = validate_translator(dagster_dbt_translator)
        manifest = validate_manifest(manifest)

        if not manifest:
            logger.info(
                "No dbt manifest was provided. Dagster events for dbt tests will not be created."
            )

        unique_id: str = event_node_info["unique_id"]
        invocation_id: str = self.raw_event["info"]["invocation_id"]
        dbt_resource_props = manifest["nodes"][unique_id]
        default_metadata = {
            **default_metadata_from_dbt_resource_props(self._event_history_metadata),
            "unique_id": unique_id,
            "invocation_id": invocation_id,
        }
        has_asset_def: bool = bool(context and context.has_assets_def)

        node_resource_type: str = event_node_info["resource_type"]
        node_status: str = event_node_info["node_status"]
        node_materialization: str = self.raw_event["data"]["node_info"]["materialized"]

        is_node_ephemeral = node_materialization == "ephemeral"
        is_node_successful = node_status == NodeStatus.Success
        is_node_finished = bool(event_node_info.get("node_finished_at"))
        if (
            node_resource_type in NodeType.refable()
            and is_node_successful
            and not is_node_ephemeral
        ):
            started_at = dateutil.parser.isoparse(event_node_info["node_started_at"])
            finished_at = dateutil.parser.isoparse(event_node_info["node_finished_at"])
            duration_seconds = (finished_at - started_at).total_seconds()

            lineage_metadata = (
                self._build_column_lineage_metadata(
                    manifest=manifest,
                    dagster_dbt_translator=dagster_dbt_translator,
                    target_path=target_path,
                )
                if target_path
                else {}
            )

            if has_asset_def:
                yield Output(
                    value=None,
                    output_name=dagster_name_fn(event_node_info),
                    metadata={
                        **default_metadata,
                        "Execution Duration": duration_seconds,
                        **adapter_response_metadata,
                        **lineage_metadata,
                    },
                )
            else:
                dbt_resource_props = manifest["nodes"][unique_id]
                asset_key = dagster_dbt_translator.get_asset_key(dbt_resource_props)

                yield AssetMaterialization(
                    asset_key=asset_key,
                    metadata={
                        **default_metadata,
                        "Execution Duration": duration_seconds,
                        **adapter_response_metadata,
                        **lineage_metadata,
                    },
                )
        elif manifest and node_resource_type == NodeType.Test and is_node_finished:
            upstream_unique_ids: List[str] = manifest["parent_map"][unique_id]
            test_resource_props = manifest["nodes"][unique_id]
            metadata = {
                **default_metadata,
                "status": node_status,
                **adapter_response_metadata,
            }

            is_asset_check = dagster_dbt_translator.settings.enable_asset_checks
            attached_node_unique_id = test_resource_props.get("attached_node")
            is_generic_test = bool(attached_node_unique_id)

            if has_asset_def and is_asset_check and is_generic_test:
                is_test_successful = node_status == TestStatus.Pass
                severity = (
                    AssetCheckSeverity.WARN
                    if node_status == TestStatus.Warn
                    else AssetCheckSeverity.ERROR
                )

                attached_node_resource_props: Dict[str, Any] = manifest["nodes"].get(
                    attached_node_unique_id
                ) or manifest["sources"].get(attached_node_unique_id)
                attached_node_asset_key = dagster_dbt_translator.get_asset_key(
                    attached_node_resource_props
                )

                yield AssetCheckResult(
                    passed=is_test_successful,
                    asset_key=attached_node_asset_key,
                    check_name=event_node_info["node_name"],
                    metadata=metadata,
                    severity=severity,
                )
            else:
                for upstream_unique_id in upstream_unique_ids:
                    upstream_resource_props: Dict[str, Any] = manifest["nodes"].get(
                        upstream_unique_id
                    ) or manifest["sources"].get(upstream_unique_id)
                    upstream_asset_key = dagster_dbt_translator.get_asset_key(
                        upstream_resource_props
                    )

                    yield AssetObservation(
                        asset_key=upstream_asset_key,
                        metadata=metadata,
                    )

    def _process_adapter_response_metadata(
        self, adapter_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process the adapter response metadata for a dbt CLI event.

        The main interface for AdapterResponse is found at https://github.com/dbt-labs/dbt-adapters.

        Currently, we pre-process the following dbt adapters, which have custom responses:

        - https://github.com/dbt-labs/dbt-bigquery: BigQueryAdapterResponse
        - https://github.com/databricks/dbt-databricks: DatabricksAdapterResponse
        - https://github.com/dbt-labs/dbt-snowflake: SnowflakeAdapterResponse
        - https://github.com/starburstdata/dbt-trino: TrinoAdapterResponse
        """
        allowlisted_adapter_response_keys = [
            # AdapterResponse
            *[
                "rows_affected",
            ],
            # BigQueryAdapterResponse
            *[
                "bytes_processed",
                "bytes_billed",
                "job_id",
                "slot_ms",
            ],
            # DatabricksAdapterResponse, SnowflakeAdapterResponse, TrinoAdapterResponse
            *[
                "query_id",
            ],
        ]

        processed_adapter_response = {
            key: value
            for key, value in adapter_response.items()
            if (key in allowlisted_adapter_response_keys and value)
        }

        return processed_adapter_response

    def _build_column_lineage_metadata(
        self,
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
        target_path: Path,
    ) -> Dict[str, Any]:
        """Process the lineage metadata for a dbt CLI event.

        Args:
            manifest (Mapping[str, Any]): The dbt manifest blob.
            dagster_dbt_translator (DagsterDbtTranslator): The translator for dbt nodes to Dagster assets.
            target_path (Path): The path to the dbt target folder.

        Returns:
            Dict[str, Any]: The lineage metadata.
        """
        if (
            # The dbt project name is only available from the manifest in `dbt-core>=1.6`.
            version.parse(dbt_version) < version.parse("1.6.0")
            # Column lineage can only be built if initial metadata is provided.
            or not self.has_column_lineage_metadata
        ):
            return {}

        event_node_info: Dict[str, Any] = self.raw_event["data"].get("node_info")
        unique_id: str = event_node_info["unique_id"]
        dbt_resource_props: Dict[str, Any] = manifest["nodes"][unique_id]

        # If the unique_id is a seed, then we don't need to process lineage.
        if unique_id.startswith("seed"):
            return {}

        # 1. Retrieve the current node's SQL file and its parents' column schemas.
        sqlglot_mapping_schema = MappingSchema()
        for relation_name, relation_metadata in self._event_history_metadata["parents"].items():
            sqlglot_mapping_schema.add_table(
                table=relation_name,
                column_mapping={
                    column_name: column_metadata["data_type"]
                    for column_name, column_metadata in relation_metadata["columns"].items()
                },
            )

        node_sql_path = target_path.joinpath(
            "run", manifest["metadata"]["project_name"], dbt_resource_props["original_file_path"]
        )
        node_ast = parse_one(sql=node_sql_path.read_text()).expression
        optimized_node_ast = cast(
            exp.Query,
            optimize(
                node_ast,
                schema=sqlglot_mapping_schema,
                validate_qualify_columns=False,  # Don't throw an error if we can't qualify a column without ambiguity.
            ),
        )

        # 2. Retrieve the column names from the current node.
        column_names = cast(exp.Query, optimized_node_ast).named_selects

        # 3. For each column, retrieve its dependencies on upstream columns from direct parents.
        deps_by_column: Dict[str, Sequence[TableColumnDep]] = {}
        for column_name in column_names:
            dbt_parent_resource_props_by_alias: Dict[str, Dict[str, Any]] = {
                parent_dbt_resource_props["alias"]: parent_dbt_resource_props
                for parent_dbt_resource_props in map(
                    lambda parent_unique_id: manifest["nodes"][parent_unique_id],
                    dbt_resource_props["depends_on"]["nodes"],
                )
            }

            column_deps: Sequence[TableColumnDep] = []
            for sqlglot_lineage_node in lineage(
                column=column_name, sql=optimized_node_ast, schema=sqlglot_mapping_schema
            ).walk():
                column = sqlglot_lineage_node.expression.find(exp.Column)
                if column and column.table in dbt_parent_resource_props_by_alias:
                    parent_resource_props = dbt_parent_resource_props_by_alias[column.table]
                    parent_asset_key = dagster_dbt_translator.get_asset_key(parent_resource_props)

                    column_deps.append(
                        TableColumnDep(asset_key=parent_asset_key, column_name=column.name)
                    )

            deps_by_column[column_name] = column_deps

        # 4. Render the lineage as metadata.
        return dict(
            TableMetadataEntries(column_lineage=TableColumnLineage(deps_by_column=deps_by_column))
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
    log_level: Literal["info", "debug"]
    context: Optional[OpExecutionContext] = field(default=None, repr=False)
    termination_timeout_seconds: float = field(
        init=False, default=DAGSTER_DBT_TERMINATION_TIMEOUT_SECONDS
    )
    _stdout: List[str] = field(init=False, default_factory=list)
    _error_messages: List[str] = field(init=False, default_factory=list)

    @classmethod
    def run(
        cls,
        args: List[str],
        env: Dict[str, str],
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
        project_dir: Path,
        target_path: Path,
        raise_on_error: bool,
        log_level: Literal["info", "debug"],
        context: Optional[OpExecutionContext],
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
            log_level=log_level,
            context=context,
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

        return self.process.wait() == 0

    @public
    def stream(
        self,
    ) -> Iterator[
        Union[
            Output,
            AssetMaterialization,
            AssetObservation,
            AssetCheckResult,
        ]
    ]:
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
        for event in self.stream_raw_events():
            yield from event.to_default_asset_events(
                manifest=self.manifest,
                dagster_dbt_translator=self.dagster_dbt_translator,
                context=self.context,
                target_path=self.target_path,
            )

    @public
    def stream_raw_events(self) -> Iterator[DbtCliEventMessage]:
        """Stream the events from the dbt CLI process.

        Returns:
            Iterator[DbtCliEventMessage]: An iterator of events from the dbt CLI process.
        """
        event_history_metadata_by_unique_id: Dict[str, Dict[str, Any]] = {}

        for log in self._stdout or self._stream_stdout():
            try:
                raw_event: Dict[str, Any] = orjson.loads(log)
                unique_id: Optional[str] = raw_event["data"].get("node_info", {}).get("unique_id")
                event_history_metadata: Dict[str, Any] = {}
                if unique_id and raw_event["info"]["name"] == "NodeFinished":
                    event_history_metadata = copy.deepcopy(
                        event_history_metadata_by_unique_id.get(unique_id, {})
                    )

                event = DbtCliEventMessage(
                    raw_event=raw_event, event_history_metadata=event_history_metadata
                )

                is_error_message = event.log_level == "error"
                is_debug_message = event.log_level == "debug"
                is_debug_user_log_level = self.log_level == "debug"

                # Parse the error message from the event, if it exists.
                if is_error_message:
                    self._error_messages.append(str(event))

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

                # Only write debug logs to stdout if the user explicitly set
                # the log level to debug.
                if not is_debug_message or is_debug_user_log_level:
                    sys.stdout.write(str(event) + "\n")
                    sys.stdout.flush()

                yield event
            except:
                # If we can't parse the log, then just emit it as a raw log.
                sys.stdout.write(log + "\n")
                sys.stdout.flush()

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

    def _stream_stdout(self) -> Iterator[str]:
        """Stream the stdout from the dbt CLI process."""
        try:
            if not self.process.stdout or self.process.stdout.closed:
                return

            with self.process.stdout:
                for raw_line in self.process.stdout or []:
                    log: str = raw_line.decode().strip()

                    yield log
        except DagsterExecutionInterruptedError:
            logger.info(f"Forwarding interrupt signal to dbt command: `{self.dbt_command}`.")

            self.process.send_signal(signal.SIGINT)
            self.process.wait(timeout=self.termination_timeout_seconds)

            raise

    def _format_error_messages(self) -> str:
        """Format the error messages from the dbt CLI process."""
        if not self._error_messages:
            return ""

        error_description = "\n".join(self._error_messages)

        return f"\n\nErrors parsed from dbt logs:\n{error_description}"

    def _raise_on_error(self) -> None:
        """Ensure that the dbt CLI process has completed. If the process has not successfully
        completed, then optionally raise an error.
        """
        is_successful = self.is_successful()

        logger.info(f"Finished dbt command: `{self.dbt_command}`.")

        if not is_successful and self.raise_on_error:
            log_path = self.target_path.joinpath("dbt.log")
            extra_description = ""

            if log_path.exists():
                extra_description = f", or view the dbt debug log: {log_path}"

            raise DagsterDbtCliRuntimeError(
                description=(
                    f"The dbt CLI process with command `{self.dbt_command}` failed with exit code"
                    f" {self.process.returncode}. Check the stdout in the Dagster compute logs for"
                    f" the full information about the error{extra_description}."
                    f"{self._format_error_messages()}"
                ),
            )


class DbtCliResource(ConfigurableResource):
    """A resource used to execute dbt CLI commands.

    Attributes:
        project_dir (str): The path to the dbt project directory. This directory should contain a
            `dbt_project.yml`. See https://docs.getdbt.com/reference/dbt_project.yml for more
            information.
        global_config_flags (List[str]): A list of global flags configuration to pass to the dbt CLI
            invocation. See https://docs.getdbt.com/reference/global-configs for a full list of
            configuration.
        profiles_dir (Optional[str]): The path to the directory containing your dbt `profiles.yml`.
            By default, the current working directory is used, which is the dbt project directory.
            See https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more
            information.
        profile (Optional[str]): The profile from your dbt `profiles.yml` to use for execution. See
            https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more
            information.
        target (Optional[str]): The target from your dbt `profiles.yml` to use for execution. See
            https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more
            information.
        dbt_executable (str): The path to the dbt executable. By default, this is `dbt`.

    Examples:
        Creating a dbt resource with only a reference to ``project_dir``:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(project_dir="/path/to/dbt/project")

        Creating a dbt resource with a custom ``profiles_dir``:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(
                project_dir="/path/to/dbt/project",
                profiles_dir="/path/to/dbt/project/profiles",
            )

        Creating a dbt resource with a custom ``profile`` and ``target``:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(
                project_dir="/path/to/dbt/project",
                profiles_dir="/path/to/dbt/project/profiles",
                profile="jaffle_shop",
                target="dev",
            )

        Creating a dbt resource with global configs, e.g. disabling colored logs with ``--no-use-color``:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(
                project_dir="/path/to/dbt/project",
                global_config_flags=["--no-use-color"],
            )

        Creating a dbt resource with custom dbt executable path:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(
                project_dir="/path/to/dbt/project",
                dbt_executable="/path/to/dbt/executable",
            )
    """

    project_dir: str = Field(
        description=(
            "The path to your dbt project directory. This directory should contain a"
            " `dbt_project.yml`. See https://docs.getdbt.com/reference/dbt_project.yml for more"
            " information."
        ),
    )
    global_config_flags: List[str] = Field(
        default=[],
        description=(
            "A list of global flags configuration to pass to the dbt CLI invocation. See"
            " https://docs.getdbt.com/reference/global-configs for a full list of configuration."
        ),
    )
    profiles_dir: Optional[str] = Field(
        default=None,
        description=(
            "The path to the directory containing your dbt `profiles.yml`. By default, the current"
            " working directory is used, which is the dbt project directory."
            " See https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for "
            " more information."
        ),
    )
    profile: Optional[str] = Field(
        default=None,
        description=(
            "The profile from your dbt `profiles.yml` to use for execution. See"
            " https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more"
            " information."
        ),
    )
    target: Optional[str] = Field(
        default=None,
        description=(
            "The target from your dbt `profiles.yml` to use for execution. See"
            " https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more"
            " information."
        ),
    )
    dbt_executable: str = Field(
        default=DBT_EXECUTABLE,
        description="The path to the dbt executable.",
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

    @validator("project_dir", "profiles_dir", "dbt_executable", pre=True)
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

    @validator("project_dir")
    def validate_project_dir(cls, project_dir: str) -> str:
        resolved_project_dir = cls._validate_absolute_path_exists(project_dir)

        cls._validate_path_contains_file(
            path=resolved_project_dir,
            file_name=DBT_PROJECT_YML_NAME,
            error_message=(
                f"{resolved_project_dir} does not contain a {DBT_PROJECT_YML_NAME} file. Please"
                " specify a valid path to a dbt project."
            ),
        )

        return os.fspath(resolved_project_dir)

    @validator("profiles_dir")
    def validate_profiles_dir(cls, profiles_dir: Optional[str]) -> Optional[str]:
        if profiles_dir is None:
            return None

        resolved_profiles_dir = cls._validate_absolute_path_exists(profiles_dir)

        cls._validate_path_contains_file(
            path=resolved_profiles_dir,
            file_name=DBT_PROFILES_YML_NAME,
            error_message=(
                f"{resolved_profiles_dir} does not contain a {DBT_PROFILES_YML_NAME} file. Please"
                " specify a valid path to a dbt profile directory."
            ),
        )

        return os.fspath(resolved_profiles_dir)

    @validator("dbt_executable")
    def validate_dbt_executable(cls, dbt_executable: str) -> str:
        resolved_dbt_executable = shutil.which(dbt_executable)
        if not resolved_dbt_executable:
            raise ValueError(
                f"The dbt executable '{dbt_executable}' does not exist. Please specify a valid"
                " path to a dbt executable."
            )

        return dbt_executable

    @compat_model_validator(mode="before")
    def validate_dbt_version(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the dbt version is supported."""
        if version.parse(dbt_version) < version.parse("1.5.0"):
            raise ValueError(
                "To use `dagster_dbt.DbtCliResource`, you must use `dbt-core>=1.5.0`. Currently,"
                f" you are using `dbt-core=={dbt_version}`. Please install a compatible dbt-core"
                " version."
            )

        return values

    def _get_unique_target_path(self, *, context: Optional[OpExecutionContext]) -> Path:
        """Get a unique target path for the dbt CLI invocation.

        Args:
            context (Optional[OpExecutionContext]): The execution context.

        Returns:
            str: A unique target path for the dbt CLI invocation.
        """
        unique_id = str(uuid.uuid4())[:7]
        path = unique_id
        if context:
            path = f"{context.op.name}-{context.run.run_id[:7]}-{unique_id}"

        current_target_path = _get_dbt_target_path()

        return current_target_path.joinpath(path)

    @public
    def cli(
        self,
        args: List[str],
        *,
        raise_on_error: bool = True,
        manifest: Optional[DbtManifestParam] = None,
        dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
        context: Optional[Union[OpExecutionContext, AssetExecutionContext]] = None,
        target_path: Optional[Path] = None,
    ) -> DbtCliInvocation:
        """Create a subprocess to execute a dbt CLI command.

        Args:
            args (List[str]): The dbt CLI command to execute.
            raise_on_error (bool): Whether to raise an exception if the dbt CLI command fails.
            manifest (Optional[Union[Mapping[str, Any], str, Path]]): The dbt manifest blob. If an
                execution context from within `@dbt_assets` is provided to the context argument,
                then the manifest provided to `@dbt_assets` will be used.
            dagster_dbt_translator (Optional[DagsterDbtTranslator]): The translator to link dbt
                nodes to Dagster assets. If an execution context from within `@dbt_assets` is
                provided to the context argument, then the dagster_dbt_translator provided to
                `@dbt_assets` will be used.
            context (Optional[Union[OpExecutionContext, AssetExecutionContext]]): The execution context from within `@dbt_assets`.
                If an AssetExecutionContext is passed, its underlying OpExecutionContext will be used.
            target_path (Optional[Path]): An explicit path to a target folder to use to store and
                retrieve dbt artifacts when running a dbt CLI command. If not provided, a unique
                target path will be generated.

        Returns:
            DbtCliInvocation: A invocation instance that can be used to retrieve the output of the
                dbt CLI command.

        Examples:
            Streaming Dagster events for dbt asset materializations and observations:

            .. code-block:: python

                from pathlib import Path

                from dagster import AssetExecutionContext
                from dagster_dbt import DbtCliResource, dbt_assets


                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                    yield from dbt.cli(["run"], context=context).stream()

            Retrieving a dbt artifact after streaming the Dagster events:

            .. code-block:: python

                from pathlib import Path

                from dagster import AssetExecutionContext
                from dagster_dbt import DbtCliResource, dbt_assets


                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                    dbt_run_invocation = dbt.cli(["run"], context=context)

                    yield from dbt_run_invocation.stream()

                    # Retrieve the `run_results.json` dbt artifact as a dictionary:
                    run_results_json = dbt_run_invocation.get_artifact("run_results.json")

                    # Retrieve the `run_results.json` dbt artifact as a file path:
                    run_results_path = dbt_run_invocation.target_path.joinpath("run_results.json")

            Customizing the asset materialization metadata when streaming the Dagster events:

            .. code-block:: python

                from pathlib import Path

                from dagster import AssetExecutionContext
                from dagster_dbt import DbtCliResource, dbt_assets


                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                    dbt_cli_invocation = dbt.cli(["run"], context=context)

                    for dagster_event in dbt_cli_invocation.stream():
                        if isinstance(dagster_event, Output):
                            context.add_output_metadata(
                                metadata={
                                    "my_custom_metadata": "my_custom_metadata_value",
                                },
                                output_name=dagster_event.output_name,
                            )

                        yield dagster_event

            Suppressing exceptions from a dbt CLI command when a non-zero exit code is returned:

            .. code-block:: python

                from pathlib import Path

                from dagster import AssetExecutionContext
                from dagster_dbt import DbtCliResource, dbt_assets


                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                    dbt_run_invocation = dbt.cli(["run"], context=context, raise_on_error=False)

                    if dbt_run_invocation.is_successful():
                        yield from dbt_run_invocation.stream()
                    else:
                        ...

            Invoking a dbt CLI command in a custom asset or op:

            .. code-block:: python

                import json

                from dagster import asset, op
                from dagster_dbt import DbtCliResource


                @asset
                def my_dbt_asset(dbt: DbtCliResource):
                    dbt_macro_args = {"key": "value"}
                    dbt.cli(["run-operation", "my-macro", json.dumps(dbt_macro_args)]).wait()


                @op
                def my_dbt_op(dbt: DbtCliResource):
                    dbt_macro_args = {"key": "value"}
                    dbt.cli(["run-operation", "my-macro", json.dumps(dbt_macro_args)]).wait()
        """
        dagster_dbt_translator = validate_opt_translator(dagster_dbt_translator)

        assets_def: Optional[AssetsDefinition] = None
        with suppress(DagsterInvalidPropertyError):
            assets_def = context.assets_def if context else None

        context = (
            context.op_execution_context if isinstance(context, AssetExecutionContext) else context
        )

        target_path = target_path or self._get_unique_target_path(context=context)
        env = {
            **os.environ.copy(),
            # An environment variable to indicate that the dbt CLI is being invoked from Dagster.
            "DAGSTER_DBT_CLI": "true",
            # Run dbt with unbuffered output.
            "PYTHONUNBUFFERED": "1",
            # Disable anonymous usage statistics for performance.
            "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
            # The DBT_LOG_FORMAT environment variable must be set to `json`. We use this
            # environment variable to ensure that the dbt CLI outputs structured logs.
            "DBT_LOG_FORMAT": "json",
            # The DBT_DEBUG environment variable must be set to `true`. We use this
            # environment variable to ensure that the dbt CLI logs have enriched metadata.
            "DBT_DEBUG": "true",
            # The DBT_TARGET_PATH environment variable is set to a unique value for each dbt
            # invocation so that artifact paths are separated.
            # See https://discourse.getdbt.com/t/multiple-run-results-json-and-manifest-json-files/7555
            # for more information.
            "DBT_TARGET_PATH": os.fspath(target_path),
            # The DBT_LOG_PATH environment variable is set to the same value as DBT_TARGET_PATH
            # so that logs for each dbt invocation has separate log files.
            "DBT_LOG_PATH": os.fspath(target_path),
            # The DBT_PROFILES_DIR environment variable is set to the path containing the dbt
            # profiles.yml file.
            # See https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles#advanced-customizing-a-profile-directory
            # for more information.
            **({"DBT_PROFILES_DIR": self.profiles_dir} if self.profiles_dir else {}),
        }

        # Although we always set the dbt log level to debug, we only write those logs to stdout if
        # the user has explicitly set the log level to debug.
        log_level = (
            "debug"
            if set(["--debug", "-d"]).intersection([*args, *self.global_config_flags])
            else "info"
        )

        selection_args: List[str] = []
        dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()
        if context and assets_def is not None:
            manifest, dagster_dbt_translator = get_manifest_and_translator_from_dbt_assets(
                [assets_def]
            )

            # When dbt is enabled with asset checks, we turn off any indirection with dbt selection.
            # This way, the Dagster context completely determines what is executed in a dbt
            # invocation.
            if dagster_dbt_translator.settings.enable_asset_checks:
                logger.info(
                    "Setting environment variable `DBT_INDIRECT_SELECTION` to 'empty'. When dbt "
                    "tests are modeled as asset checks, they are executed through explicit selection."
                )
                env["DBT_INDIRECT_SELECTION"] = "empty"

            selection_args = get_subset_selection_for_context(
                context=context,
                manifest=manifest,
                select=context.op.tags.get(DAGSTER_DBT_SELECT_METADATA_KEY),
                exclude=context.op.tags.get(DAGSTER_DBT_EXCLUDE_METADATA_KEY),
                dagster_dbt_translator=dagster_dbt_translator,
            )
        else:
            manifest = validate_manifest(manifest) if manifest else {}

        # TODO: verify that args does not have any selection flags if the context and manifest
        # are passed to this function.
        profile_args: List[str] = []
        if self.profile:
            profile_args = ["--profile", self.profile]

        if self.target:
            profile_args += ["--target", self.target]

        args = [
            self.dbt_executable,
            *self.global_config_flags,
            *args,
            *profile_args,
            *selection_args,
        ]
        project_dir = Path(self.project_dir)

        if not target_path.is_absolute():
            target_path = project_dir.joinpath(target_path)

        return DbtCliInvocation.run(
            args=args,
            env=env,
            manifest=manifest,
            dagster_dbt_translator=dagster_dbt_translator,
            project_dir=project_dir,
            target_path=target_path,
            raise_on_error=raise_on_error,
            log_level=log_level,
            context=context,
        )


def get_subset_selection_for_context(
    context: OpExecutionContext,
    manifest: Mapping[str, Any],
    select: Optional[str],
    exclude: Optional[str],
    dagster_dbt_translator: DagsterDbtTranslator,
) -> List[str]:
    """Generate a dbt selection string to materialize the selected resources in a subsetted execution context.

    See https://docs.getdbt.com/reference/node-selection/syntax#how-does-selection-work.

    Args:
        context (OpExecutionContext): The execution context for the current execution step.
        select (Optional[str]): A dbt selection string to select resources to materialize.
        exclude (Optional[str]): A dbt selection string to exclude resources from materializing.

    Returns:
        List[str]: dbt CLI arguments to materialize the selected resources in a
            subsetted execution context.

            If the current execution context is not performing a subsetted execution,
            return CLI arguments composed of the inputed selection and exclusion arguments.
    """
    default_dbt_selection = []
    if select:
        default_dbt_selection += ["--select", select]
    if exclude:
        default_dbt_selection += ["--exclude", exclude]

    dbt_resource_props_by_output_name = get_dbt_resource_props_by_output_name(manifest)
    dbt_resource_props_by_test_name = get_dbt_resource_props_by_test_name(manifest)

    # It's nice to use the default dbt selection arguments when not subsetting for readability.
    # However with asset checks, we make a tradeoff between readability and functionality for the user.
    # This is because we use an explicit selection of each individual dbt resource we execute to ensure
    # we control which models *and tests* run. By using explicit selection, we allow the user to
    # also subset the execution of dbt tests.
    if not context.is_subset and not dagster_dbt_translator.settings.enable_asset_checks:
        logger.info(
            "A dbt subsetted execution is not being performed. Using the default dbt selection"
            f" arguments `{default_dbt_selection}`."
        )
        return default_dbt_selection

    selected_dbt_resources = []
    for output_name in context.selected_output_names:
        dbt_resource_props = dbt_resource_props_by_output_name[output_name]

        # Explicitly select a dbt resource by its fully qualified name (FQN).
        # https://docs.getdbt.com/reference/node-selection/methods#the-file-or-fqn-method
        fqn_selector = f"fqn:{'.'.join(dbt_resource_props['fqn'])}"

        selected_dbt_resources.append(fqn_selector)

    for _, check_name in context.selected_asset_check_keys:
        test_resource_props = dbt_resource_props_by_test_name[check_name]

        # Explicitly select a dbt resource by its fully qualified name (FQN).
        # https://docs.getdbt.com/reference/node-selection/methods#the-file-or-fqn-method
        fqn_selector = f"fqn:{'.'.join(test_resource_props['fqn'])}"

        selected_dbt_resources.append(fqn_selector)

    # Take the union of all the selected resources.
    # https://docs.getdbt.com/reference/node-selection/set-operators#unions
    union_selected_dbt_resources = ["--select"] + [" ".join(selected_dbt_resources)]

    if context.is_subset:
        logger.info(
            "A dbt subsetted execution is being performed. Overriding default dbt selection"
            f" arguments `{default_dbt_selection}` with arguments: `{union_selected_dbt_resources}`"
        )
    else:
        logger.info(
            "A dbt subsetted execution is not being performed. Because asset checks are enabled,"
            f" converting the default dbt selection arguments `{default_dbt_selection}` with the "
            f"explicit set of models and tests: `{union_selected_dbt_resources}`"
        )

    return union_selected_dbt_resources


def get_dbt_resource_props_by_output_name(
    manifest: Mapping[str, Any],
) -> Mapping[str, Mapping[str, Any]]:
    node_info_by_dbt_unique_id = get_dbt_resource_props_by_dbt_unique_id_from_manifest(manifest)

    return {
        dagster_name_fn(node): node
        for node in node_info_by_dbt_unique_id.values()
        if node["resource_type"] in ASSET_RESOURCE_TYPES
    }


def get_dbt_resource_props_by_test_name(
    manifest: Mapping[str, Any],
) -> Mapping[str, Mapping[str, Any]]:
    return {
        dbt_resource_props["name"]: dbt_resource_props
        for unique_id, dbt_resource_props in manifest["nodes"].items()
        if unique_id.startswith("test")
    }
