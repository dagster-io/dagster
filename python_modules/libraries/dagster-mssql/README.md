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

**Collation does not matter.** Dagster's text columns are `NVARCHAR` on SQL Server, so
asset keys, partition keys and run tags containing non-ASCII characters are stored
correctly under any collation — including on SQL Server 2017, where UTF-8 collations are
not available.

**Bounded identifier columns.** SQL Server cannot index `NVARCHAR(max)`, so columns that
appear in an index key are bounded (asset keys at 256 characters, partition and step keys
at 128, and so on) rather than unbounded. Postgres has a comparable btree key limit, and
MySQL indexes only a 64-character prefix of these same columns. A value that exceeds the
bound is rejected rather than silently truncated.

## Testing

The tests need Docker. `pytest` brings up a SQL Server container via
`dagster_mssql_tests/docker-compose.yml`, creates the test database, and runs Dagster's
shared storage suites against it:

```sh
tox -e py312-storage_tests
```
