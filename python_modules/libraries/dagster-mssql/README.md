# dagster-mssql

Microsoft SQL Server storage for Dagster: run storage, event log storage and schedule
storage, backed by SQL Server 2017+, Azure SQL Database, or Azure SQL Managed Instance.

The docs for `dagster-mssql` can be found
[here](https://docs.dagster.io/integrations/libraries/mssql/dagster-mssql).

## Requirements

`dagster-mssql` connects through [pyodbc](https://github.com/mkleehammer/pyodbc), which
dispatches to a locally installed ODBC driver. Install
[Microsoft ODBC Driver 18 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
(or 17) on every host that runs Dagster — the webserver, the daemon, and any code
location.

## Configuration

In `$DAGSTER_HOME/dagster.yaml`, either give a full URL:

```yaml
storage:
  mssql:
    mssql_url: "mssql+pyodbc://user:password@host:1433/dagster?driver=ODBC+Driver+18+for+SQL+Server"
```

or configure the parts separately:

```yaml
storage:
  mssql:
    mssql_db:
      username: dagster
      password:
        env: DAGSTER_MSSQL_PASSWORD
      hostname: sqlserver.example.com
      db_name: dagster
      port: 1433
      driver: "ODBC Driver 18 for SQL Server"
      params:
        Encrypt: "yes"
```

Every field is a `StringSource`/`IntSource`, so any of them can be read from an
environment variable as shown above. Anything under `params` is passed through to the ODBC
driver, which is where connection options such as `Encrypt`, `TrustServerCertificate`,
`Authentication` (for Entra ID against Azure SQL) and `MultiSubnetFailover` belong.

## Notes on SQL Server

**Enable read-committed snapshot.** SQL Server's default `READ COMMITTED` takes shared
read locks, so the daemon and the webserver will block each other under load. Postgres
does not behave this way, and neither does SQL Server once you run:

```sql
ALTER DATABASE dagster SET READ_COMMITTED_SNAPSHOT ON;
```

This is left to whoever provisions the database: it is a database-wide setting, it needs
elevated permissions, and it briefly requires exclusive access.

**Upserts retry on deadlock.** SQL Server has no `INSERT .. ON CONFLICT`, so dagster's
upserts are `MERGE ... WITH (HOLDLOCK, UPDLOCK)`, which is serializable. At that isolation
level SQL Server protects a key *range* rather than a row, so two processes writing
different rows — two daemons sending heartbeats, or materializing unrelated assets — can
still be picked as deadlock victims. That is expected rather than a fault, and SQL Server's
own message says what to do about it: rerun the transaction. `dagster-mssql` does, with
jittered backoff. Deadlocks logged at DEBUG by `dagster_mssql.utils` are normal under load;
a `DagsterMSSQLException` mentioning the deadlock victim means the retries were exhausted,
which is worth investigating.

**Collation does not matter.** Dagster's text columns are `NVARCHAR` on SQL Server, so
asset keys, partition keys and run tags containing non-ASCII characters are stored
correctly under any collation — including on SQL Server 2017, where UTF-8 collations are
not available.

**Bounded identifier columns.** SQL Server cannot index `NVARCHAR(max)`, so columns that
appear in an index key are bounded (asset keys at 256 characters, partition and step keys
at 128, and so on) rather than unbounded. Postgres has a comparable btree key limit, and
MySQL indexes only a 64-character prefix of these same columns. A value that exceeds the
bound is rejected rather than silently truncated.

## Schema migrations

`dagster-mssql` ships its own Alembic revision tree under `dagster_mssql/alembic/`, rather
than sharing the one in `dagster` core the way `dagster-mysql` and `dagster-postgres` do.
Core's tree carries per-dialect branches whose DDL is not valid on SQL Server.

The consequence is that **new core migrations are not inherited**. A fresh SQL Server
deployment is unaffected — it builds its schema with `create_all()` and stamps the head —
so a missing migration is invisible until an existing deployment runs
`dagster instance migrate` and silently receives nothing.

`dagster_mssql/alembic/__init__.py` records `SYNCED_TO_CORE_REVISION`, the head of core's
tree this one was last reconciled against.
`dagster_mssql_tests/test_migrations.py::TestCoreRevisionParity` fails as soon as core's
head moves, and names the revisions that appeared. When that happens, each new core
revision must either be ported to `dagster_mssql/alembic/versions/` or recorded in
`CORE_REVISIONS_NOT_APPLICABLE` with the reason it does not apply — and only then may
`SYNCED_TO_CORE_REVISION` be advanced.

Schema snapshots for back-compatibility testing live in `dagster_mssql_tests/compat_tests/`;
see that module's docstring for how to capture one.

## Testing

The tests need Docker. `pytest` brings up a SQL Server container via
`dagster_mssql_tests/docker-compose.yml`, creates the test database, and runs Dagster's
shared storage suites against it:

```sh
tox -e py312-storage_tests
```
