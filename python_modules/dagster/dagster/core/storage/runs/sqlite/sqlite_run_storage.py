import os
from contextlib import contextmanager
from urllib.parse import urljoin, urlparse

import sqlalchemy as db
from dagster import StringSource, check
from dagster.core.storage.sql import (
    check_alembic_revision,
    create_engine,
    get_alembic_config,
    handle_schema_errors,
    run_alembic_downgrade,
    run_alembic_upgrade,
    stamp_alembic_rev,
)
from dagster.core.storage.sqlite import create_db_conn_string
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils import mkdir_p
from sqlalchemy.pool import NullPool

from ..schema import RunStorageSqlMetadata, RunTagsTable, RunsTable
from ..sql_run_storage import SqlRunStorage


class SqliteRunStorage(SqlRunStorage, ConfigurableClass):
    """SQLite-backed run storage.

    Users should not directly instantiate this class; it is instantiated by internal machinery when
    ``dagit`` and ``dagster-graphql`` load, based on the values in the ``dagster.yaml`` file in
    ``$DAGSTER_HOME``. Configuration of this class should be done by setting values in that file.

    This is the default run storage when none is specified in the ``dagster.yaml``.

    To explicitly specify SQLite for run storage, you can add a block such as the following to your
    ``dagster.yaml``:

    .. code-block:: YAML

        run_storage:
          module: dagster.core.storage.runs
          class: SqliteRunStorage
          config:
            base_dir: /path/to/dir

    The ``base_dir`` param tells the run storage where on disk to store the database.
    """

    def __init__(self, conn_string, inst_data=None):
        check.str_param(conn_string, "conn_string")
        self._conn_string = conn_string
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": StringSource}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SqliteRunStorage.from_local(inst_data=inst_data, **config_value)

    @staticmethod
    def from_local(base_dir, inst_data=None):
        check.str_param(base_dir, "base_dir")
        mkdir_p(base_dir)
        conn_string = create_db_conn_string(base_dir, "runs")
        engine = create_engine(conn_string, poolclass=NullPool)
        alembic_config = get_alembic_config(__file__)

        should_mark_indexes = False
        with engine.connect() as connection:
            db_revision, head_revision = check_alembic_revision(alembic_config, connection)
            if not (db_revision and head_revision):
                RunStorageSqlMetadata.create_all(engine)
                engine.execute("PRAGMA journal_mode=WAL;")
                stamp_alembic_rev(alembic_config, connection)
                should_mark_indexes = True

        run_storage = SqliteRunStorage(conn_string, inst_data)

        if should_mark_indexes:
            # mark all secondary indexes
            run_storage.build_missing_indexes()

        return run_storage

    @contextmanager
    def connect(self):
        engine = create_engine(self._conn_string, poolclass=NullPool)
        conn = engine.connect()
        try:
            with handle_schema_errors(
                conn,
                get_alembic_config(__file__),
                msg="Sqlite run storage requires migration",
            ):
                yield conn
        finally:
            conn.close()

    def _alembic_upgrade(self, rev="head"):
        alembic_config = get_alembic_config(__file__)
        with self.connect() as conn:
            run_alembic_upgrade(alembic_config, conn, rev=rev)

    def _alembic_downgrade(self, rev="head"):
        alembic_config = get_alembic_config(__file__)
        with self.connect() as conn:
            run_alembic_downgrade(alembic_config, conn, rev=rev)

    def upgrade(self):
        self._check_for_version_066_migration_and_perform()
        self._alembic_upgrade()

    # In version 0.6.6, we changed the layout of the of the sqllite dbs on disk
    # to move from the root of DAGSTER_HOME/runs.db to DAGSTER_HOME/history/runs.bd
    # This function checks for that condition and does the move
    def _check_for_version_066_migration_and_perform(self):
        old_conn_string = "sqlite://" + urljoin(urlparse(self._conn_string).path, "../runs.db")
        path_to_old_db = urlparse(old_conn_string).path
        # sqlite URLs look like `sqlite:///foo/bar/baz on Unix/Mac` but on Windows they look like
        # `sqlite:///D:/foo/bar/baz` (or `sqlite:///D:\foo\bar\baz`)
        if os.name == "nt":
            path_to_old_db = path_to_old_db.lstrip("/")
        if os.path.exists(path_to_old_db):
            old_storage = SqliteRunStorage(old_conn_string)
            old_runs = old_storage.get_runs()
            for run in old_runs:
                self.add_run(run)
            os.unlink(path_to_old_db)

    def delete_run(self, run_id):
        """Override the default sql delete run implementation until we can get full
        support on cascading deletes"""
        check.str_param(run_id, "run_id")
        remove_tags = db.delete(RunTagsTable).where(RunTagsTable.c.run_id == run_id)
        remove_run = db.delete(RunsTable).where(RunsTable.c.run_id == run_id)
        with self.connect() as conn:
            conn.execute(remove_tags)
            conn.execute(remove_run)
