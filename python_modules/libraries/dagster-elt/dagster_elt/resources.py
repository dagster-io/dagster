import contextlib
import os
import tempfile
from enum import Enum
from subprocess import PIPE, STDOUT, Popen
from typing import Any, Dict, Generator, List, Optional

import yaml
from dagster import Config, ConfigurableResource, get_dagster_logger
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


class SlingSource(Config):
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

    source_connection: Optional[str] = Field(
        description="The Sling source connection string, often a database connection string."
    )
    target_connection: str = Field(description="Connection string for the target database")

    def _get_env_config(self) -> Dict[str, str]:
        return {"connections": "test"}

    @contextlib.contextmanager
    def _setup_config(self) -> Generator[None, None, None]:
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "env.yaml"), "w") as f:
                f.write(yaml.dump(self._get_env_config()))
            with environ({"SLING_HOME_DIR": temp_dir}):
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
        source_conn: str,
        target_conn: str,
        source_table: str,
        dest_table: str,
        mode: SlingMode = SlingMode.FULL_REFRESH,
        primary_key: Optional[List[str]] = None,
        update_key: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Runs a Sling sync from the given source table to the given destination table. Generates
        output lines from the Sling CLI.
        """
        with self._setup_config():
            config = {
                "source": {
                    "conn": source_conn,
                    "stream": source_table,
                    **(
                        {
                            "primary_key": primary_key,
                        }
                        if primary_key
                        else {}
                    ),
                    **(
                        {
                            "update_key": update_key,
                        }
                        if update_key
                        else {}
                    ),
                },
                "target": {
                    "conn": target_conn,
                    "object": dest_table,
                },
                "mode": mode.value,
            }

            sling_cli = Sling(**config)

            logger.info("Starting Sling sync with mode: %s", mode)
            cmd = sling_cli._prep_cmd()  # noqa: SLF001

            yield from self.exec_sling_cmd(cmd)

    def sync(
        self, source: SlingSource, target: SlingTarget, mode: SlingMode
    ) -> Generator[str, None, None]:
        """Syncs the source and target objects."""
        yield from self._sync(
            source_conn=self.source_connection,
            target_conn=self.target_connection,
            source_table=source.stream,
            dest_table=target.object,
            mode=mode,
            primary_key=source.primary_key,
            update_key=source.update_key,
        )
