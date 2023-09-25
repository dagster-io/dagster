import contextlib
import json
import tempfile
from enum import Enum
from subprocess import PIPE, STDOUT, Popen
from typing import Any, Dict, Generator, List, Optional

from dagster import Config, ConfigurableResource, PermissiveConfig, get_dagster_logger
from dagster._utils.env import environ
from pydantic import Field
from sling import Sling  # type: ignore

logger = get_dagster_logger()


class SlingMode(str, Enum):
    """The mode to use when syncing.
    See the Sling docs for more information: https://docs.slingdata.io/sling-cli/running-tasks#modes.
    """

    INCREMENTAL = "incremental"
    TRUNCATE = "truncate"
    FULL_REFRESH = "full-refresh"
    SNAPSHOT = "snapshot"


class SlingSourceConfig(Config):
    """Sling Source configuration.


    See the docs for more information:
    https://docs.slingdata.io/sling-cli/running-tasks#cli-flags-yaml-keys

    """

    stream: Optional[str] = Field(
        description=(
            "The source table (schema.table) or local / cloud file path. Can also be the path of"
            " sql file or in-line text."
        )
    )
    primary_key: Optional[List[str]] = Field(description="The column(s) to use as primary key.")
    update_key: Optional[List[str]] = Field(
        description="The column(s) to use as update key. If not provided, primary key will be used."
    )
    limit: Optional[int] = Field(
        description=(
            "The number of rows to fetch from the source. If not provided, all rows will be "
            "fetched."
        )
    )

    options: Optional[Dict[str, Any]] = Field(
        description="Additional options to pass to the source. See Sling docs for more details."
    )


class SlingTarget(Config):
    object: str = Field(
        description=(
            "The target table (schema.table) or local / cloud file path. Can also be the path of"
        )
    )


class SlingSourceConnection(PermissiveConfig):
    type: str = Field(description="Type of the source connection. Use 'file' for local storage.")
    connection_string: Optional[str] = Field(
        description="The connection string for the source database."
    )


class SlingTargetConnection(PermissiveConfig):
    type: str = Field(
        description="Type of the destination connection. Use 'file' for local storage."
    )
    connection_string: Optional[str] = Field(
        description="The connection string for the target database."
    )


class SlingResource(ConfigurableResource):
    """Resource for interacting with the Sling package.

    Examples:
        .. code-block:: python
        from dagster import Definitions, asset
        from dagster_etl import SlingResource

        @asset
        def sync_asset(sling: SlingResource):
            res = sling.sync()
            for stdout in res:
                context.log.info(stdout)

        defs = Definitions(
            assets=[sync_asset],
            resources={"sling": SlingResource(
                source=SlingSource(
                    stream="file:///path/to/file.csv",
                    primary_key=["SPECIES_CODE"],
                ),
                target=SlingTarget(
                    connection="sqlite:///path/to/sqlite.db",
                    object="main.tbl",
                ),
                mode=SlingMode.TRUNCATE,
            )}
        )
    """

    source_connection: SlingSourceConnection
    target_connection: SlingTargetConnection

    def _get_env_config(self) -> Dict[str, Any]:
        return {
            "connections": {
                "sling_source": repr(self.source_connection.dict()),
            }
        }

    @contextlib.contextmanager
    def _setup_config(self) -> Generator[None, None, None]:
        with environ(
            {
                "SLING_SOURCE": json.dumps(self.source_connection.dict()),
                "SLING_TARGET": json.dumps(self.target_connection.dict()),
            }
        ):
            yield

    def exec_sling_cmd(
        self, cmd, stdin=None, stdout=PIPE, stderr=STDOUT
    ) -> Generator[str, None, None]:
        # copied from
        # https://github.com/slingdata-io/sling-python/blob/main/sling/__init__.py#L251
        # fixes issue w/ trying to gather stderr when stderr=STDOUT
        with Popen(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr) as proc:
            assert proc.stdout

            for line in proc.stdout:
                fmt_line = str(line.strip(), "utf-8")
                yield fmt_line

            proc.wait()
            if proc.returncode != 0:
                raise Exception("Sling command failed with error code %s", proc.returncode)

    def _sync(
        self,
        source_stream: str,
        target_object: str,
        mode: SlingMode = SlingMode.FULL_REFRESH,
        primary_key: Optional[List[str]] = None,
        update_key: Optional[str] = None,
        source_options: Optional[Dict[str, Any]] = None,
        target_options: Optional[Dict[str, Any]] = None,
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

            yield from self.exec_sling_cmd(cmd)

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
        """Syncs the source and target objects."""
        yield from self._sync(
            source_stream=source_stream,
            target_object=target_object,
            mode=mode,
            primary_key=primary_key,
            update_key=update_key,
            source_options=source_options,
            target_options=target_options,
        )
