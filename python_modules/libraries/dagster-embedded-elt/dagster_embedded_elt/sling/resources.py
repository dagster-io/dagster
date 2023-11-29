import contextlib
import json
import re
from enum import Enum
from subprocess import PIPE, STDOUT, Popen
from typing import IO, Any, AnyStr, Dict, Generator, Iterator, List, NamedTuple, Optional, Union

from dagster import ConfigurableResource, PermissiveConfig, get_dagster_logger
from dagster._annotations import experimental
from dagster._utils.env import environ
from pydantic import ConfigDict, Extra, Field
from sling import Sling

logger = get_dagster_logger()


class SlingMode(str, Enum):
    """The mode to use when syncing.

    See the Sling docs for more information: https://docs.slingdata.io/sling-cli/running-tasks#modes.
    """

    INCREMENTAL = "incremental"
    TRUNCATE = "truncate"
    FULL_REFRESH = "full-refresh"
    SNAPSHOT = "snapshot"


class SlingStream(NamedTuple):
    stream_name: str
    object: Optional[str] = None
    mode: Optional[SlingMode] = None
    primary_key: Optional[Union[str, List[str]]] = None
    update_key: Optional[str] = None
    sql: Optional[str] = None
    disabled: Optional[bool] = False


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


class SlingSyncBase:
    def process_stdout(self, stdout: IO[AnyStr], encoding="utf8") -> Iterator[str]:
        """Process stdout from the Sling CLI."""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        for line in stdout:
            assert isinstance(line, bytes)
            fmt_line = bytes.decode(line, encoding=encoding, errors="replace")
            clean_line: str = ansi_escape.sub("", fmt_line).replace("INF", "")
            yield clean_line

    def _exec_sling_cmd(
        self, cmd, stdin=None, stdout=PIPE, stderr=STDOUT, encoding="utf8"
    ) -> Generator[str, None, None]:
        with Popen(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr) as proc:
            if proc.stdout:
                for line in self.process_stdout(proc.stdout, encoding=encoding):
                    yield line

            proc.wait()
            if proc.returncode != 0:
                raise Exception("Sling command failed with error code %s", proc.returncode)

    def _override_config(self, cmd: str, config: Dict[str, Any]) -> None:
        """Override the config file for the Sling CLI with the given config."""
        _sling_bin, _run, _c, temp_file = cmd.split(" ")
        temp_file = temp_file[1:-1]

        with open(temp_file, "w") as f:
            json.dump(config, f)


@experimental
class SlingResource(ConfigurableResource, SlingSyncBase):
    """Resource for interacting with the Sling package.

    Examples:
        .. code-block:: python

            from dagster_etl.sling import SlingResource
            sling_resource = SlingResource(
                source_connection=SlingSourceConnection(
                    type="postgres", connection_string=EnvVar("POSTGRES_CONNECTION_STRING")
                ),
                target_connection=SlingTargetConnection(
                    type="snowflake",
                    host="host",
                    user="user",
                    database="database",
                    password="password",
                    role="role",
                ),
            )

    """

    source_connection: SlingSourceConnection
    target_connection: SlingTargetConnection

    @contextlib.contextmanager
    def _setup_config(self) -> Generator[None, None, None]:
        """Uses environment variables to set the Sling source and target connections."""
        sling_source = dict(self.source_connection)
        sling_target = dict(self.target_connection)

        if self.source_connection.connection_string:
            sling_source["url"] = self.source_connection.connection_string
        if self.target_connection.connection_string:
            sling_target["url"] = self.target_connection.connection_string
        with environ(
            {
                "SLING_SOURCE": json.dumps(sling_source),
                "SLING_TARGET": json.dumps(sling_target),
            }
        ):
            yield

    def sync(
        self,
        source_stream: str,
        target_object: str,
        mode: SlingMode,
        primary_key: Optional[List[str]] = None,
        update_key: Optional[str] = None,
        source_options: Optional[Dict[str, Any]] = None,
        target_options: Optional[Dict[str, Any]] = None,
    ) -> Generator[str, None, None]:
        """Initiate a Sling Sync between a source stream and a target object.

        Args:
            source_stream (str):  The source stream to read from. For database sources, the source stream can be either
                a table name, a SQL statement or a path to a SQL file e.g. `TABLE1` or `SCHEMA1.TABLE2` or
                `SELECT * FROM TABLE`. For file sources, the source stream is a path or an url to a file.
                For file targets, the target object is a path or a url to a file, e.g. file:///tmp/file.csv or
                s3://my_bucket/my_folder/file.csv
            target_object (str): The target object to write into. For database targets, the target object is a table
                name, e.g. TABLE1, SCHEMA1.TABLE2. For file targets, the target object is a path or an url to a file.
            mode (SlingMode): The Sling mode to use when syncing, i.e. incremental, full-refresh
                See the Sling docs for more information: https://docs.slingdata.io/sling-cli/running-tasks#modes.
            primary_key (List[str]): For incremental syncs, a primary key is used during merge statements to update
                existing rows.
            update_key (str): For incremental syncs, an update key is used to stream records after max(update_key)
            source_options (Dict[str, Any]): Other source options to pass to Sling,
                see https://docs.slingdata.io/sling-cli/running-tasks#source-options-src-options-flag-source.options-key
                for details
            target_options (Dict[str, Any[): Other target options to pass to Sling,
                see https://docs.slingdata.io/sling-cli/running-tasks#target-options-tgt-options-flag-target.options-key
                for details

        Examples:
            Sync from a source file to a sqlite database:

            .. code-block:: python

                sqllite_path = "/path/to/sqlite.db"
                csv_path = "/path/to/file.csv"

                @asset
                def run_sync(context, sling: SlingResource):
                    res = sling.sync(
                        source_stream=csv_path,
                        target_object="events",
                        mode=SlingMode.FULL_REFRESH,
                    )
                    for stdout in res:
                        context.log.debug(stdout)
                    counts = sqlite3.connect(sqllitepath).execute("SELECT count(1) FROM events").fetchone()
                    assert counts[0] == 3

                source = SlingSourceConnection(
                    type="file",
                )
                target = SlingTargetConnection(type="sqlite", instance=sqllitepath)

                materialize(
                    [run_sync],
                    resources={
                        "sling": SlingResource(
                            source_connection=source,
                            target_connection=target,
                            mode=SlingMode.TRUNCATE,
                        )
                    },
                )

        """
        yield from self._sync(
            source_stream=source_stream,
            target_object=target_object,
            mode=mode,
            primary_key=primary_key,
            update_key=update_key,
            source_options=source_options,
            target_options=target_options,
        )

    def _sync(
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
        output lines from the Sling CLI.
        """
        if self.source_connection.type == "file" and not source_stream.startswith("file://"):
            source_stream = "file://" + source_stream

        if self.target_connection.type == "file" and not target_object.startswith("file://"):
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

            sling_cli = Sling(**config)
            logger.info("Starting Sling sync with mode: %s", mode)
            cmd = sling_cli._prep_cmd()  # noqa: SLF001

            yield from self._exec_sling_cmd(cmd, encoding=encoding)


class SlingConnectionResource(ConfigurableResource):
    """A representation a connection to a database or file to be used by Sling. This resource can be used as a source or a target for a Sling sync.

    This resource is responsible for the managing how Sling connects to a resource. To manage how Sling uses this connection (as a source or target), see the specific source_options or target_options in the `build_assets_from_sling_stream` function.

    Examples:
        Creating a Sling Connection for a file, such as CSV or JSON:

        .. code-block:: python

             source = SlingConnectionResource(type="file")

        Create a Sling Connection for a Postgres database, using a connection string:

        .. code-block:: python

            source = SlingConnectionResource(type="postgres", connection_string=EnvVar("POSTGRES_CONNECTION_STRING"))
            source = SlingConnectionResource(type="mysql", connection_string="mysql://user:password@host:port/schema")

        Create a Sling Connection for a Postgres or Snowflake database, using keyword arguments, as described here:
        https://docs.slingdata.io/connections/database-connections/postgres

        .. code-block::python

            source = SlingConnectionResource(type="postgres", host="host", user="hunter42", password=EnvVar("POSTGRES_PASSWORD"))
            source = SlingConnectionResource(type="snowflake", host=EnvVar("SNOWFLAKE_HOST"), user=EnvVar("SNOWFLAKE_USER"), database=EnvVar("SNOWFLAKE_DATABASE"), password=EnvVar("SNOWFLAKE_PASSWORD"), role=EnvVar("SNOWFLAKE_ROLE"))
    """

    model_config = ConfigDict(extra=Extra.allow)

    type: str = Field(description="Type of the source connection. Use 'file' for local storage.")
    connection_string: Optional[str] = Field(
        description="The connection string for the source database.",
        default=None,
    )


class SlingStreamReplicator(SlingSyncBase):
    """A utility class for running a Sling sync from outside of a Dagster resource to enable parity between the SlingResource and SlingStreamSync.

    Inherits from :py:class:`~dagster_elt.sling.SlingSyncBase` and implements `_sync` to run a sync using 2 SlingConnectionResources and no SlingResource.
    """

    def __init__(
        self,
        source_connection: SlingConnectionResource,
        target_connection: SlingConnectionResource,
    ):
        self.source_connection = source_connection
        self.target_connection = target_connection

    def sync(
        self,
        streams: List[Dict[str, Any]],
        mode: SlingMode,
        target_object: str,
        source_options: Optional[Dict[str, Any]] = None,
        target_options: Optional[Dict[str, Any]] = None,
    ) -> Generator[str, None, None]:
        yield from self._sync(
            streams=streams,
            mode=mode,
            target_object=target_object,
            source_options=source_options,
            target_options=target_options,
        )

    def _sync(
        self,
        streams: List[Dict[str, Any]],
        mode: SlingMode,
        target_object: str,
        source_options: Optional[Dict[str, Any]] = None,
        target_options: Optional[Dict[str, Any]] = None,
        encoding: str = "utf8",
    ) -> Generator[str, None, None]:
        """Runs a Sling sync from the given source table to the given destination table. Generates
        output lines from the Sling CLI.
        """
        if self.target_connection.type == "file" and not target_object.startswith("file://"):
            target_object = "file://" + target_object

        sling_source = self.source_connection.dict()
        sling_target = self.target_connection.dict()

        if self.source_connection.connection_string:
            sling_source["url"] = self.source_connection.connection_string
        if self.target_connection.connection_string:
            sling_target["url"] = self.target_connection.connection_string
        with environ(
            {
                "SLING_SOURCE": json.dumps(sling_source),
                "SLING_TARGET": json.dumps(sling_target),
            }
        ):
            stream_config = {}

            for stream in streams:
                filtered_config = {
                    k: v
                    for k, v in stream.items()
                    if v is not None and v is not False and k != "stream_name"
                }

                if filtered_config.get("primary_key"):
                    filtered_config["primary_key"] = [filtered_config["primary_key"]]

                stream_config[stream["stream_name"]] = filtered_config if filtered_config else None

            config = {
                "source": "SLING_SOURCE",
                "target": "SLING_TARGET",
                "defaults": {
                    "mode": mode,
                    "object": target_object,
                    "source_options": source_options,
                    "target_options": target_options,
                },
                "streams": {
                    **stream_config,
                },
                "streams": {f"{source_stream}": None},
            }
            stream_config["defaults"] = {
                k: v for k, v in stream_config["defaults"].items() if v is not None
            }
            config["defaults"] = {k: v for k, v in config["defaults"].items() if v is not None}

            sling_cli = Sling()
            logger.info("Starting Sling sync with mode: %s", mode)
            cmd = sling_cli._prep_cmd()  # noqa: SLF001

            # write the SLING_TARGET and SLING_SOURCE to a file in cwd
            with open("sling_config.json", "w") as f:
                json.dump(config, f)

            self._override_config(cmd, config)
            cmd = cmd.replace(" -c ", " -r ")

            yield from self._exec_sling_cmd(cmd, encoding=encoding)
