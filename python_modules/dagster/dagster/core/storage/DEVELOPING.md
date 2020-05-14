## Changing Persistence

Feature development in Dagster often requires changes to underlying storage. We have made the design choice to allow for pluggability in the system. While this increases flexibility it also places burdens on Dagster developers, as you will see.

This document will cover the process of changing persistence in event log, runs, and/or schedule storage.

As a system developer if one changes the interface for any one of those storage, you will be supporting three different implementations: in-memory, sqlite, and postgres.

### Process:

(Note: for the following steps we are going to use the run storage as an example. Please substitute appropriate classes for other storage varietals.)

**Write the actual code**:

- Change the common interface (e.g. `RunStorage`).
- Implement the new capabilities in the in-memory version variant (e.g. `InMemoryRunStorage`).
- Implement the sql variant (e.g. `SqlRunStorage`) which is generic to both postgres and mysql for most features. You must change the core schema definitions (e.g. `dagster.core.storage.runs.schema`). Later, when you make migrations work, duplicate this schema in a migration script. You must keep these in sync.
- There is a convenient, generic test suite common to all run storages (`TestRunStorage`). If one does not exist for the store that you are changing, you are highly encouraged to add a common testing facility like this for other storage types that do not have it.

**Writing Database Migrations**:

- As alluded to above, you have to think about migrations whenever you do database changes. We manage migrations using alembic (https://alembic.sqlalchemy.org/en/latest/). We are actively and frequently developing features that require schema changes and data migrations, and our users need to run these migrations on their own infrastructure to get these new features. This is dangerous and tricky work, and therefore we need to have discipline and testing around it.

- The first step is to create the migration script with alembic for sqlite. E.g. run `alembic revision -m "some new feature"` at `python_modules/dagster/dagster/core/storage/runs/sqlite/alembic` which will create a stub file.
- Within that file you must write the actual migration. The migration should be idempotent. See `python_modules/dagster/dagster/core/storage/runs/sqlite/alembic/versions/c63a27054f08_add_snapshots_to_run_storage.py` for an example.
- Repeat the process for postgres. Generally the contents of this file will be very similar or identical to the sqlite version. However there are differences between the setups so there may be in need of customization. The postgres version has the particularity that there must be a byte-for-byte copy of the migration script in every store's versions folder. This is because dagster can run with those stores in the same database or in separate databases. These scripts must be replicated for alembic's tracking to work in both cases. Browse the `event_log`, `schedule_storage`, and `run_storage` folders in `python_modules/libraries/dagster-postgres/dagster_postgres` to see this in action. The invariant of having identical files is part of our test suite.

**Testing Database Migrations**:

- Migrations are potentially dangerous and difficult to get right, so we test them. This type of work is important in keeping faith with the user base we serve, so they can continue to upgrade dagster with confidence as it develops and matures. The general process involves grabbing copies of databases created with the previous version of the code, and then running `DagsterInstance.upgrade` on that historical instance. The old copies of the database must be checked into source control.
- Sqlite snapshot: First let's grab the sqlite snapshot. Sqlite is the default configuration running dagster from the command line. Alternatively you can invoke `execute_pipeline` with the argument `instance=DagsterInstance.get()`. Run a pipeline or otherwise create state in the database that will exercise the schema/data migration properly during the upgrade process. For the runs example, `cp ~/.dagster/history` (or your custom instance location) into `python_modules/dagster/dagster_tests/compat_tests/snapshot_versionnumber_yourfeature`. Then find an example test in that test suite and mimic it for your migration.
- Postgres snapshot: Reconstructing a postgres database requires the `pg_dump` tool, include with the postgres tools. You will need to install these tools on your machine. (See: https://blog.timescale.com/tutorials/how-to-install-psql-on-mac-ubuntu-debian-windows/ for an example). Similar to the sqlite process, you will want to generate state in the database that exercises your specific migration. In this case you'll have to configure the dagster instance to point to postgres. Something similar to:

```
run_storage:
 module: dagster_postgres.run_storage
 class: PostgresRunStorage
 config:
   postgres_db:
     username: test
     password: test
     hostname: localhost
     db_name: migration_add_snapshot_db
     port: 5432
event_log_storage:
 module: dagster_postgres.event_log
 class: PostgresEventLogStorage
 config:
   postgres_db:
     username: test
     password: test
     hostname: localhost
     db_name: migration_add_snapshot_db
     port: 5432

schedule_storage:
 module: dagster_postgres.schedule_storage
 class: PostgresScheduleStorage
 config:
   postgres_db:
     username: test
     password: test
     hostname: localhost
     db_name: migration_add_snapshot_db
     port: 5432
```

- Then run pgdump. E.g.: `pg_dump --dbname=migration_add_snapshot_db --host=localhost --port=5432 --username=test > pg_dump_add_snapshot_db.txt`
- Copy the exported file an appropriately named folder as other folders in `python_modules/libraries/dagster-postgres/dagster_postgres_tests/compat_tests` with the identical structure.
- To write your tests, find a test in that test suite and mimic it.
