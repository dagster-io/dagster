# Storage migrations

We use alembic (https://alembic.sqlalchemy.org/en/latest/) to manage the schema migrations for our storage. This adds a directory of migration scripts to your repo and an alembic_version table to your database to keep track of which migration scripts have been applied.

## Adding a schema migration

Migrations are only required when you are altering the schema of an existing table (adding/removing a column, adding an index, etc).

To add a sql schema migration, follow the following steps:

1. Change the schema definition
   1. add a column foo to RunsTable in dagster.core.storage.runs.schema
1. Add an alembic migration script. You'll typically use a specific engine (e.g. sqlite) to create the script, but the migration will apply to all storage implementations
   1. `cd python_modules/dagster/dagster/_core/storage/runs/sqlite/alembic; alembic revision -m 'add column foo'`
   1. Fill in the upgrade/downgrade parts of the migration using alembic operations: `op.add_column('runs', db.Column('foo', db.String))`
   1. Make sure that any storage-specific changes are guarded (e.g. if this should only apply to run storage, then do a `runs` table existence check)
   1. Make sure that any dialect-specific changes are guarded (e.g. if this should only apply to MySQL, then wrap in a conditional).

Users should be prompted to manually run migrations using `dagster instance migrate`.

## Testing a schema migration

For schema migrations, we test migration behavior in sqlite / postgres / mysql.

For all backcompat schema migrations, the back compat tests should have the following structure:
1. Load an instance from a DB snapshot
1. Assert that the migrations have not been run
1. Test the affected storage methods using the pre-migrated snapshot, if the functionality existed pre-migration
1. Run the migration
1. Test the affected storage methods post-migration

### sqlite

Migration tests for sqlite can be found here: `python_modules/dagster/dagster_tests/general_tests/compat_tests/test_back_compat.py`

To add a new back-compat test for sqlite, follow the following steps:

1. Switch code branches to master or some revision before you’ve added the schema change.
1. Change your dagster.yaml to use the default sqlite implementation for run/event_log storage.
1. Make sure your configured storage directory (e.g. $DAGSTER_HOME/history) is wiped
1. Start dagit and execute a pipeline run, to ensure that both the run db and per-run event_log dbs are created.
1. Copy the runs.db and all per-run event log dbs to the back compat test directory:
   - `mkdir -p python_modules/dagster/dagster_tests/general_tests/compat_tests/<my_schema_change>/sqlite/history`
   - `cp $DAGSTER_HOME/history/runs.db\* python_modules/dagster/dagster_tests/general_tests/compat_tests/<my_schema_change>/sqlite/history/`
   - `cp -R $DAGSTER_HOME/history/runs python_modules/dagster/dagster_tests/general_tests/compat_tests/<my_schema_change>/sqlite/history/`
1. Write your back compat test, loading your snapshot directory

### postgres

Migration tests for postgres can be found here: `python_modules/libraries/dagster-postgres/dagster_postgres_tests/compat_tests/test_back_compat.py`

To add a new back-compat test for postgres, follow the following steps:

1. Switch code branches to master or some revision before you’ve added the schema change.
1. Change your dagster.yaml to use a wiped postgres storage configuration
   ```
   event_log_storage:
     module: dagster_postgres.event_log
     class: PostgresEventLogStorage
     config:
       postgres_url: "postgresql://test:test@localhost:5432/test"
   run_storage:
     module: dagster_postgres.run_storage
     class: PostgresRunStorage
     config:
       postgres_url: "postgresql://test:test@localhost:5432/test"
   schedule_storage:
     module: dagster_postgres.schedule_storage
     class: PostgresScheduleStorage
     config:
       postgres_url: "postgresql://test:test@localhost:5432/test"
   ```
1. Wipe, if you haven’t already dagster run wipe
1. Start dagit and execute a pipeline run, to ensure that both the run db and per-run event_log dbs are created.
1. Create a pg dump file
   - `mkdir python_modules/libraries/dagster-postgres/dagster_postgres_tests/compat_tests/<my_schema_change>/postgres`
   - `pg_dump test > python_modules/libraries/dagster-postgres/dagster_postgres_tests/compat_tests/<my_schema_change>/postgres/pg_dump.txt`
1. Write your back compat test, loading your snapshot directory

### mysql

Migration tests for mysql can be found here:
REPO_ROOT/python_modules/libraries/dagster-mysql/dagster_mysql_tests/compat_tests/test_back_compat.py

To add a new back-compat test for mysql, follow the following steps:

1. Switch code branches to master or some revision before you’ve added the schema change.
2. Change your dagster.yaml to use a wiped postgres storage configuration
   ```
   event_log_storage:
     module: dagster_mysql.event_log
     class: MySQLEventLogStorage
     config:
       mysql_url: "mysql+mysqlconnector://test:test@localhost:3306/test"
   run_storage:
     module: dagster_mysql.run_storage
     class: MySQLRunStorage
     config:
       mysql_url: "mysql+mysqlconnector://test:test@localhost:3306/test"
   schedule_storage:
     module: dagster_mysql.schedule_storage
     class: MySQLScheduleStorage
     config:
       mysql_url: "mysql+mysqlconnector://test:test@localhost:3306/test"
   ```
3. Wipe, if you haven’t already dagster run wipe
4. Start dagit and execute a pipeline run, to ensure that both the run db and per-run event_log dbs are created.
5. Create a mysql dump file
   - `mkdir python_modules/libraries/dagster-mysql/dagster_mysql_tests/compat_tests/<my_schema_change>/mysql`
   - `mysqldump test > python_modules/libraries/dagster-mysql/dagster_mysql_tests/compat_tests/<my_schema_change>/mysql/mysql_dump.sql -p`
6. Write your back compat test, loading your snapshot directory

### Adding a data migration

Generally we do not want to force users to data migrations, especially over the event log which might be extremely large and therefore expensive.

For secondary index tables (e.g. derived tables from event_log), you can write your custom data migration script, and mark the status of the migration in the secondary_indexes table. This allows you to write guards in your EventLogStorage class that optionally reads from the event log or from the secondary index table, depending on the status of the migration.

See `EventLogStorage.has_secondary_index` and `EventLogStorage.enable_secondary_index` for more.

Users should be prompted to manually run data migrations using `dagster instance reindex`.
