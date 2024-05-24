import contextlib
import json
import os
import re
import sys
import tempfile
import time
import uuid
from enum import Enum
from subprocess import PIPE, STDOUT, Popen
from typing import IO, Any, AnyStr, Dict, Generator, Iterator, List, Optional, Union

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
from dagster._annotations import deprecated, experimental, public
from dagster._utils.env import environ
from dagster._utils.warnings import deprecation_warning
from pydantic import Field

from dagster_embedded_elt.sling.asset_decorator import (
    METADATA_KEY_REPLICATION_CONFIG,
    METADATA_KEY_TRANSLATOR,
    get_streams_from_replication,
    streams_with_default_dagster_meta,
)
from dagster_embedded_elt.sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_embedded_elt.sling.sling_replication import SlingReplicationParam, validate_replication

logger = get_dagster_logger()

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
DEPRECATION_WARNING_TEXT = "{name} has been deprecated, use `SlingConnectionResource` for both source and target connections."


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


@deprecated(
    breaking_version="0.23.0",
    additional_warn_text=DEPRECATION_WARNING_TEXT.format(name="SlingSourceConnection"),
)
class SlingSourceConnection(PermissiveConfig):
    """A Sling Source Connection defines the source connection used by :py:class:`~dagster_elt.sling.SlingResource`.

    Examples:
        Creating a Sling Source for a file, such as CSV or JSON:

        .. code-block:: python

             source = SlingSourceConnection(type="file")

        Create a Sling Source for a Postgres database, using a connection string:

        .. code-block:: python

            source = SlingTargetConnection(type="postgres", connection_string=EnvVar("POSTGRES_CONNECTION_STRING"))
            source = SlingSourceConnection(type="postgres", connection_string="postgresql://user:password@host:port/schema")

        Create a Sling Source for a Postgres database, using keyword arguments, as described here:
        https://docs.slingdata.io/connections/database-connections/postgres

        .. code-block:: python

            source = SlingTargetConnection(type="postgres", host="host", user="hunter42", password=EnvVar("POSTGRES_PASSWORD"))

    """

    type: str = Field(description="Type of the source connection. Use 'file' for local storage.")
    connection_string: Optional[str] = Field(
        description="The connection string for the source database.",
        default=None,
    )


@deprecated(
    breaking_version="0.23.0",
    additional_warn_text=DEPRECATION_WARNING_TEXT.format(name="SlingTargetConnection"),
)
class SlingTargetConnection(PermissiveConfig):
    """A Sling Target Connection defines the target connection used by :py:class:`~dagster_elt.sling.SlingResource`.

    Examples:
        Creating a Sling Target for a file, such as CSV or JSON:

        .. code-block:: python

             source = SlingTargetConnection(type="file")

        Create a Sling Source for a Postgres database, using a connection string:

        .. code-block:: python

            source = SlingTargetConnection(type="postgres", connection_string="postgresql://user:password@host:port/schema"
            source = SlingTargetConnection(type="postgres", connection_string=EnvVar("POSTGRES_CONNECTION_STRING"))

        Create a Sling Source for a Postgres database, using keyword arguments, as described here:
        https://docs.slingdata.io/connections/database-connections/postgres

        .. code-block::python

            source = SlingTargetConnection(type="postgres", host="host", user="hunter42", password=EnvVar("POSTGRES_PASSWORD"))


    """

    type: str = Field(
        description="Type of the destination connection. Use 'file' for local storage."
    )
    connection_string: Optional[str] = Field(
        description="The connection string for the target database.",
        default=None,
    )


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


@experimental
class SlingResource(ConfigurableResource):
    """Resource for interacting with the Sling package. This resource can be used to run Sling replications.

    Args:
        connections (List[SlingConnectionResource]): A list of connections to use for the replication.
        source_connection (Optional[SlingSourceConnection]): Deprecated, use `connections` instead.
        target_connection (Optional[SlingTargetConnection]): Deprecated, use `connections` instead.

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

    source_connection: Optional[SlingSourceConnection] = None
    target_connection: Optional[SlingTargetConnection] = None
    connections: List[SlingConnectionResource] = []
    _stdout: List[str] = []

    @staticmethod
    def _get_replication_streams_for_context(
        context: Union[OpExecutionContext, AssetExecutionContext],
    ) -> Dict[str, Any]:
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
                asset_key = dagster_sling_translator.get_asset_key(stream)
                if asset_key in selected_asset_keys:
                    context_streams.update({stream["name"]: stream["config"]})

        return context_streams

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _clean_connection_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        d = _process_env_vars(d)
        if d["connection_string"]:
            d["url"] = d["connection_string"]
        if "connection_string" in d:
            del d["connection_string"]
        return d

    def prepare_environment(self) -> Dict[str, Any]:
        sling_source = None
        sling_target = None

        if self.source_connection:
            sling_source = self._clean_connection_dict(dict(self.source_connection))
        if self.target_connection:
            sling_target = self._clean_connection_dict(dict(self.target_connection))

        env = {}

        if sling_source:
            env["SLING_SOURCE"] = json.dumps(sling_source)

        if sling_target:
            env["SLING_TARGET"] = json.dumps(sling_target)

        for conn in self.connections:
            d = self._clean_connection_dict(dict(conn))
            env[conn.name] = json.dumps(d)

        return env

    @contextlib.contextmanager
    def _setup_config(self) -> Generator[None, None, None]:
        """Uses environment variables to set the Sling source and target connections."""
        if self.source_connection:
            deprecation_warning(
                "source_connection",
                "0.23",
                "source_connection has been deprecated, provide a list of SlingConnectionResource to the `connections` parameter instead.",
                stacklevel=4,
            )

        if self.target_connection:
            deprecation_warning(
                "target_connection",
                "0.23",
                "target_connection has been deprecated, provide a list of SlingConnectionResource to the `connections` parameter instead.",
                stacklevel=4,
            )

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
                for line in self._process_stdout(proc.stdout, encoding=encoding):
                    yield line

            proc.wait()
            if proc.returncode != 0:
                raise Exception("Sling command failed with error code %s", proc.returncode)

    @deprecated(
        breaking_version="0.23.0",
        additional_warn_text="sync has been deprecated, use `replicate` instead.",
    )
    def sync(
        self,
        source_stream: str,
        target_object: str,
        mode: SlingMode = SlingMode.FULL_REFRESH,
        primary_key: Optional[List[str]] = None,
        update_key: Optional[str] = None,
        source_options: Optional[Dict[str, Any]] = None,
        target_options: Optional[Dict[str, Any]] = None,
        encoding: str = "utf8",
    ) -> Generator[str, None, None]:
        """Runs a Sling sync from the given source table to the given destination table. Generates
        output lines from the Sling CLI. Deprecated, use `replicate` instead.
        """
        if (
            self.source_connection
            and self.source_connection.type == "file"
            and not source_stream.startswith("file://")
        ):
            source_stream = "file://" + source_stream

        if (
            self.target_connection
            and self.target_connection.type == "file"
            and not target_object.startswith("file://")
        ):
            target_object = "file://" + target_object

        with self._setup_config():
            config = {
                "mode": mode,
                "source": {
                    "conn": "SLING_SOURCE",
                    "stream": source_stream,
                    "primary_key": primary_key,
                    "update_key": update_key,
                    "options": source_options,
                },
                "target": {
                    "conn": "SLING_TARGET",
                    "object": target_object,
                    "options": target_options,
                },
            }
            config["source"] = {k: v for k, v in config["source"].items() if v is not None}
            config["target"] = {k: v for k, v in config["target"].items() if v is not None}

            sling_cli = sling.Sling(**config)
            logger.info("Starting Sling sync with mode: %s", mode)
            cmd = sling_cli._prep_cmd()  # noqa: SLF001

            yield from self._exec_sling_cmd(cmd, encoding=encoding)

    def replicate(
        self,
        *,
        context: Union[OpExecutionContext, AssetExecutionContext],
        replication_config: Optional[SlingReplicationParam] = None,
        dagster_sling_translator: Optional[DagsterSlingTranslator] = None,
        debug: bool = False,
    ) -> Generator[Union[MaterializeResult, AssetMaterialization], None, None]:
        """Runs a Sling replication from the given replication config.

        Args:
            context: Asset or Op execution context.
            replication_config: The Sling replication config to use for the replication.
            dagster_sling_translator: The translator to use for the replication.
            debug: Whether to run the replication in debug mode.

        Returns:
            Generator[Union[MaterializeResult, AssetMaterialization], None, None]: A generator of MaterializeResult or AssetMaterialization
        """
        # attempt to retrieve params from asset context if not passed as a parameter
        if not (replication_config or dagster_sling_translator):
            metadata_by_key = context.assets_def.metadata_by_key
            first_asset_metadata = next(iter(metadata_by_key.values()))
            dagster_sling_translator = first_asset_metadata.get(METADATA_KEY_TRANSLATOR)
            replication_config = first_asset_metadata.get(METADATA_KEY_REPLICATION_CONFIG)

        # if translator has not been defined on metadata _or_ through param, then use the default constructor
        dagster_sling_translator = dagster_sling_translator or DagsterSlingTranslator()

        # convert to dict to enable updating the index
        replication_config = dict(validate_replication(replication_config))
        context_streams = self._get_replication_streams_for_context(context)
        if context_streams:
            replication_config.update({"streams": context_streams})
        stream_definition = get_streams_from_replication(replication_config)

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

        has_asset_def: bool = bool(context and context.has_assets_def)

        for stream in stream_definition:
            output_name = dagster_sling_translator.get_asset_key(stream)
            if has_asset_def:
                yield MaterializeResult(
                    asset_key=output_name, metadata={"elapsed_time": end_time - start_time}
                )
            else:
                yield AssetMaterialization(
                    asset_key=output_name, metadata={"elapsed_time": end_time - start_time}
                )

    def stream_raw_logs(self) -> Generator[str, None, None]:
        """Returns a generator of raw logs from the Sling CLI."""
        yield from self._stdout


def _process_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for key, value in config.items():
        if isinstance(value, dict) and len(value) == 1 and next(iter(value.keys())) == "env":
            out[key] = EnvVar(next(iter(value.values()))).get_value()
        else:
            out[key] = value
    return out
