import contextlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Generator, Iterator, Sequence
from enum import Enum
from subprocess import PIPE, STDOUT, Popen
from typing import IO, Any, AnyStr, Optional, Union

import sling
from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    ConfigurableResource,
    EnvVar,
    MaterializeResult,
    OpExecutionContext,
    PermissiveConfig,
    get_dagster_logger,
)
from dagster._annotations import public
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._utils.env import environ
from pydantic import Field

from dagster_sling.asset_decorator import (
    METADATA_KEY_REPLICATION_CONFIG,
    METADATA_KEY_TRANSLATOR,
    get_streams_from_replication,
    streams_with_default_dagster_meta,
)
from dagster_sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_sling.sling_event_iterator import SlingEventIterator, SlingEventType
from dagster_sling.sling_replication import SlingReplicationParam, validate_replication

logger = get_dagster_logger()

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


@public
class SlingMode(str, Enum):
    """The mode to use when syncing.

    See the Sling docs for more information: https://docs.slingdata.io/sling-cli/run/configuration#modes
    """

    INCREMENTAL = "incremental"
    TRUNCATE = "truncate"
    FULL_REFRESH = "full-refresh"
    SNAPSHOT = "snapshot"
    BACKFILL = "backfill"


@public
class SlingConnectionResource(PermissiveConfig):
    """A representation of a connection to a database or file to be used by Sling. This resource can be used as a source or a target for a Sling syncs.

    Reference the Sling docs for more information on possible connection types and parameters: https://docs.slingdata.io/connections

    The name of the connection is passed to Sling and must match the name of the connection provided in the replication configuration: https://docs.slingdata.io/sling-cli/run/configuration/replication
    You may provide either a connection string or keyword arguments for the connection.

    Examples:
        Creating a Sling Connection for a file, such as CSV or JSON:

        .. code-block:: python

             source = SlingConnectionResource(name="MY_FILE", type="file")

        Create a Sling Connection for a Postgres database, using a connection string:

        .. code-block:: python

            postgres_conn = SlingConnectionResource(name="MY_POSTGRES", type="postgres", connection_string=EnvVar("POSTGRES_CONNECTION_STRING"))
            mysql_conn = SlingConnectionResource(name="MY_MYSQL", type="mysql", connection_string="mysql://user:password@host:port/schema")

        Create a Sling Connection for a Postgres or Snowflake database, using keyword arguments:

        .. code-block::python

            postgres_conn = SlingConnectionResource(
                name="MY_OTHER_POSRGRES",
                type="postgres",
                host="host",
                user="hunter42",
                password=EnvVar("POSTGRES_PASSWORD")
            )

            snowflake_conn = SlingConnectionResource(
                name="MY_SNOWFLAKE",
                type="snowflake",
                host=EnvVar("SNOWFLAKE_HOST"),
                user=EnvVar("SNOWFLAKE_USER"),
                database=EnvVar("SNOWFLAKE_DATABASE"),
                password=EnvVar("SNOWFLAKE_PASSWORD"),
                role=EnvVar("SNOWFLAKE_ROLE")
            )
    """

    name: str = Field(
        description="The name of the connection, must match the name in your Sling replication configuration."
    )
    type: str = Field(
        description="Type of the source connection, must match the Sling connection types. Use 'file' for local storage."
    )
    connection_string: Optional[str] = Field(
        description="The optional connection string for the source database, if not using keyword arguments.",
        default=None,
    )


class SlingResource(ConfigurableResource):
    """Resource for interacting with the Sling package. This resource can be used to run Sling replications.

    Args:
        connections (List[SlingConnectionResource]): A list of connections to use for the replication.

    Examples:
        .. code-block:: python

            from dagster_etl.sling import SlingResource, SlingConnectionResource

            sling_resource = SlingResource(
                connections=[
                    SlingConnectionResource(
                        name="MY_POSTGRES",
                        type="postgres",
                        connection_string=EnvVar("POSTGRES_CONNECTION_STRING"),
                    ),
                    SlingConnectionResource(
                        name="MY_SNOWFLAKE",
                        type="snowflake",
                        host=EnvVar("SNOWFLAKE_HOST"),
                        user=EnvVar("SNOWFLAKE_USER"),
                        database=EnvVar("SNOWFLAKE_DATABASE"),
                        password=EnvVar("SNOWFLAKE_PASSWORD"),
                        role=EnvVar("SNOWFLAKE_ROLE"),
                    ),
                ]
            )
    """

    connections: list[SlingConnectionResource] = []
    _stdout: list[str] = []

    @staticmethod
    def _get_replication_streams_for_context(
        context: Union[OpExecutionContext, AssetExecutionContext],
    ) -> dict[str, Any]:
        """Computes the sling replication streams config for a given execution context with an
        assets def, possibly involving a subset selection of sling assets.
        """
        if not context.has_assets_def:
            no_assets_def_message = """
            The current execution context has no backing AssetsDefinition object. Therefore,  no
            sling assets subsetting will be performed...
            """
            logger.warn(no_assets_def_message)
            return {}
        context_streams = {}
        assets_def = context.assets_def
        run_config = context.run_config
        if run_config:  # triggered via sensor
            run_config_ops = run_config.get("ops", {})
            if isinstance(run_config_ops, dict):
                assets_op_config = run_config_ops.get(assets_def.op.name, {}).get("config", {})
            else:
                assets_op_config = {}
            context_streams = assets_op_config.get("context_streams", {})
            if not context_streams:
                no_context_streams_config_message = f"""
                It was expected that your `run_config` would provide a `context_streams` config for
                the op {assets_def.op.name}. Instead, the received value for this op config was
                {assets_op_config}.

                NO ASSET SUBSETTING WILL BE PERFORMED!

                If that was your intention, you can safely ignore this message. Otherwise, provide
                the mentioned `context_streams` config for executing only your desired asset subset.
                """
                logger.warn(no_context_streams_config_message)
        else:
            metadata_by_key = assets_def.metadata_by_key
            first_asset_metadata = next(iter(metadata_by_key.values()))
            replication_config: dict[str, Any] = first_asset_metadata.get(
                METADATA_KEY_REPLICATION_CONFIG, {}
            )
            dagster_sling_translator: DagsterSlingTranslator = first_asset_metadata.get(
                METADATA_KEY_TRANSLATOR, DagsterSlingTranslator()
            )
            raw_streams = get_streams_from_replication(replication_config)
            streams = streams_with_default_dagster_meta(raw_streams, replication_config)
            selected_asset_keys = context.selected_asset_keys
            for stream in streams:
                asset_key = dagster_sling_translator.get_asset_spec(stream).key
                if asset_key in selected_asset_keys:
                    context_streams.update({stream["name"]: stream["config"]})

        return context_streams

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _clean_connection_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        d = _process_env_vars(d)
        if d["connection_string"]:
            d["url"] = d["connection_string"]
        if "connection_string" in d:
            del d["connection_string"]
        return d

    def prepare_environment(self) -> dict[str, Any]:
        env = {}

        for conn in self.connections:
            d = self._clean_connection_dict(dict(conn))
            env[conn.name] = json.dumps(d)

        return env

    @contextlib.contextmanager
    def _setup_config(self) -> Generator[None, None, None]:
        """Uses environment variables to set the Sling source and target connections."""
        prepared_environment = self.prepare_environment()
        with environ(prepared_environment):
            yield

    def _clean_line(self, line: str) -> str:
        """Removes ANSI escape sequences from a line of output."""
        return ANSI_ESCAPE.sub("", line).replace("INF", "")

    def _process_stdout(self, stdout: IO[AnyStr], encoding="utf8") -> Iterator[str]:
        """Process stdout from the Sling CLI."""
        for line in stdout:
            assert isinstance(line, bytes)
            fmt_line = bytes.decode(line, encoding=encoding, errors="replace")
            yield self._clean_line(fmt_line)

    def _exec_sling_cmd(
        self, cmd, stdin=None, stdout=PIPE, stderr=STDOUT, encoding="utf8"
    ) -> Generator[str, None, None]:
        with Popen(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr) as proc:
            if proc.stdout:
                yield from self._process_stdout(proc.stdout, encoding=encoding)

            proc.wait()
            if proc.returncode != 0:
                raise Exception("Sling command failed with error code %s", proc.returncode)

    def _parse_json_table_output(self, table_output: dict[str, Any]) -> list[dict[str, str]]:
        column_keys: list[str] = table_output["fields"]
        column_values: list[list[str]] = table_output["rows"]

        return [dict(zip(column_keys, column_values)) for column_values in column_values]

    def get_column_info_for_table(self, target_name: str, table_name: str) -> list[dict[str, str]]:
        """Fetches column metadata for a given table in a Sling target and parses it into a list of
        dictionaries, keyed by column name.

        Args:
            target_name (str): The name of the target connection to use.
            table_name (str): The name of the table to fetch column metadata for.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, keyed by column name, containing column metadata.
        """
        output = self.run_sling_cli(
            ["conns", "discover", target_name, "--pattern", table_name, "--columns"],
            force_json=True,
        )
        return self._parse_json_table_output(json.loads(output.strip()))

    def get_row_count_for_table(self, target_name: str, table_name: str) -> int:
        """Queries the target connection to get the row count for a given table.

        Args:
            target_name (str): The name of the target connection to use.
            table_name (str): The name of the table to fetch the row count for.

        Returns:
            int: The number of rows in the table.
        """
        select_stmt: str = f"select count(*) as ct from {table_name}"
        output = self.run_sling_cli(
            ["conns", "exec", target_name, select_stmt],
            force_json=True,
        )
        return int(
            next(iter(self._parse_json_table_output(json.loads(output.strip()))[0].values()))
        )

    def run_sling_cli(self, args: Sequence[str], force_json: bool = False) -> str:
        """Runs the Sling CLI with the given arguments and returns the output.

        Args:
            args (Sequence[str]): The arguments to pass to the Sling CLI.

        Returns:
            str: The output from the Sling CLI.
        """
        with environ({"SLING_OUTPUT": "json"}) if force_json else contextlib.nullcontext():
            return subprocess.check_output(args=[sling.SLING_BIN, *args], text=True)

    def replicate(
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        replication_config: Optional[SlingReplicationParam] = None,
        dagster_sling_translator: Optional[DagsterSlingTranslator] = None,
        debug: bool = False,
    ) -> SlingEventIterator[SlingEventType]:
        """Runs a Sling replication from the given replication config.

        Args:
            context: Asset or Op execution context.
            replication_config: The Sling replication config to use for the replication.
            dagster_sling_translator: The translator to use for the replication.
            debug: Whether to run the replication in debug mode.

        Returns:
            SlingEventIterator[MaterializeResult]: A generator of MaterializeResult
        """
        if not (replication_config or dagster_sling_translator):
            metadata_by_key = context.assets_def.metadata_by_key
            first_asset_metadata = next(iter(metadata_by_key.values()))
            dagster_sling_translator = first_asset_metadata.get(METADATA_KEY_TRANSLATOR)
            replication_config = first_asset_metadata.get(METADATA_KEY_REPLICATION_CONFIG)

        dagster_sling_translator = dagster_sling_translator or DagsterSlingTranslator()
        replication_config_dict = dict(validate_replication(replication_config))
        return SlingEventIterator(
            self._replicate(
                context=context,
                replication_config=replication_config_dict,
                dagster_sling_translator=dagster_sling_translator,
                debug=debug,
            ),
            sling_cli=self,
            replication_config=replication_config_dict,
            context=context,
        )

    def _replicate(
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        replication_config: dict[str, Any],
        dagster_sling_translator: DagsterSlingTranslator,
        debug: bool,
    ) -> Iterator[SlingEventType]:
        # if translator has not been defined on metadata _or_ through param, then use the default constructor

        # convert to dict to enable updating the index
        context_streams = self._get_replication_streams_for_context(context)
        if context_streams:
            replication_config.update({"streams": context_streams})
        stream_definitions = get_streams_from_replication(replication_config)

        # extract the destination name from the replication config
        destination_name = replication_config.get("target")

        with self._setup_config():
            uid = uuid.uuid4()
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"sling-replication-{uid}.json")
            env = os.environ.copy()

            with open(temp_file, "w") as file:
                json.dump(replication_config, file, cls=sling.JsonEncoder)

            logger.debug(f"Replication config: {replication_config}")

            debug_str = "-d" if debug else ""

            cmd = f"{sling.SLING_BIN} run {debug_str} -r {temp_file}"

            logger.debug(f"Running Sling replication with command: {cmd}")

            # Get start time from wall clock
            start_time = time.time()
            results = sling._run(  # noqa
                cmd=cmd,
                temp_file=temp_file,
                return_output=True,
                env=env,
            )
            for row in results.split("\n"):
                clean_line = self._clean_line(row)
                sys.stdout.write(clean_line + "\n")
                self._stdout.append(clean_line)

            end_time = time.time()

            # TODO: In the future, it'd be nice to yield these materializations as they come in
            # rather than waiting until the end of the replication
            for stream in stream_definitions:
                asset_key = dagster_sling_translator.get_asset_spec(stream).key

                object_key = (stream.get("config") or {}).get("object")
                destination_stream_name = object_key or stream["name"]
                table_name = None
                if destination_name and destination_stream_name:
                    table_name = ".".join([destination_name, destination_stream_name])

                metadata = {
                    "elapsed_time": end_time - start_time,
                    "stream_name": stream["name"],
                    **TableMetadataSet(
                        table_name=table_name,
                    ),
                }

                if context.has_assets_def:
                    yield MaterializeResult(asset_key=asset_key, metadata=metadata)
                else:
                    yield AssetMaterialization(asset_key=asset_key, metadata=metadata)

    def stream_raw_logs(self) -> Generator[str, None, None]:
        """Returns a generator of raw logs from the Sling CLI."""
        yield from self._stdout


def _process_env_vars(config: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for key, value in config.items():
        if isinstance(value, dict) and len(value) == 1 and next(iter(value.keys())) == "env":
            out[key] = EnvVar(next(iter(value.values()))).get_value()
        else:
            out[key] = value
    return out
