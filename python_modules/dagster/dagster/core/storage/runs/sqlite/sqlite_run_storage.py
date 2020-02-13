import os
from contextlib import contextmanager

import sqlalchemy as db
from sqlalchemy.pool import NullPool

from dagster import check
from dagster.core.serdes import ConfigurableClass, ConfigurableClassData
from dagster.seven import urljoin, urlparse
from dagster.utils import mkdir_p

from ...sql import check_alembic_revision, create_engine, get_alembic_config, stamp_alembic_rev
from ..schema import RunStorageSqlMetadata, RunTagsTable, RunsTable
from ..sql_run_storage import SqlRunStorage


class SqliteRunStorage(SqlRunStorage, ConfigurableClass):
    '''SQLite-backed run storage.

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
    '''

    def __init__(self, conn_string, inst_data=None):
        check.str_param(conn_string, 'conn_string')
        self._conn_string = conn_string
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {'base_dir': str}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SqliteRunStorage.from_local(inst_data=inst_data, **config_value)

    @staticmethod
    def from_local(base_dir, inst_data=None):
        check.str_param(base_dir, 'base_dir')
        mkdir_p(base_dir)
        path_components = os.path.abspath(base_dir).split(os.sep)
        conn_string = 'sqlite:///{}'.format('/'.join(path_components + ['runs.db']))
        engine = create_engine(conn_string, poolclass=NullPool)
        engine.execute('PRAGMA journal_mode=WAL;')
        RunStorageSqlMetadata.create_all(engine)
        alembic_config = get_alembic_config(__file__)
        connection = engine.connect()
        db_revision, head_revision = check_alembic_revision(alembic_config, connection)
        if not (db_revision and head_revision and db_revision == head_revision):
            stamp_alembic_rev(alembic_config, engine)

        return SqliteRunStorage(conn_string, inst_data)

    @contextmanager
    def connect(self):
        engine = create_engine(self._conn_string, poolclass=NullPool)
        conn = engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def upgrade(self):
        old_conn_string = 'sqlite://' + urljoin(urlparse(self._conn_string).path, '../runs.db')
        path_to_old_db = urlparse(old_conn_string).path
        # sqlite URLs look like `sqlite:///foo/bar/baz on Unix/Mac` but on Windows they look like
        # `sqlite:///D:/foo/bar/baz` (or `sqlite:///D:\foo\bar\baz`)
        if os.name == 'nt':
            path_to_old_db = path_to_old_db.lstrip('/')
        if os.path.exists(path_to_old_db):
            old_storage = SqliteRunStorage(old_conn_string)
            old_runs = old_storage.get_runs()
            for run in old_runs:
                self.add_run(run)
            os.unlink(path_to_old_db)

    def delete_run(self, run_id):
        ''' Override the default sql delete run implementation until we can get full
        support on cascading deletes '''
        check.str_param(run_id, 'run_id')
        remove_tags = db.delete(RunTagsTable).where(RunTagsTable.c.run_id == run_id)
        remove_run = db.delete(RunsTable).where(RunsTable.c.run_id == run_id)
        with self.connect() as conn:
            conn.execute(remove_tags)
            conn.execute(remove_run)
