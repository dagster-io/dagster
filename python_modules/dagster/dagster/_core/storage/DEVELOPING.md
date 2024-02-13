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
- Within that file you must write the actual migration. The migration should be idempotent. See `python_modules/dagster/dagster/_core/storage/alembic/versions/` for examples.

**Testing Database Migrations**:

- Migrations are potentially dangerous and difficult to get right, so we test them. This type of work is important in keeping faith with the user base we serve, so they can continue to upgrade dagster with confidence as it develops and matures. The general process involves grabbing copies of databases created with the previous version of the code, and then running `DagsterInstance.upgrade` on that historical instance. The old copies of the database must be checked into source control.
- The full process is outlined in [our alembic README.md](https://github.com/dagster-io/dagster/tree/master/python_modules/dagster/dagster/_core/storage/alembic)
