---
title: 'dagster-mssql integration reference'
description: SQL Server behavior that differs from Postgres and MySQL, and what to do about it.
sidebar_position: 200
---

This page covers the ways SQL Server differs from the other storage backends. Configuration is on the [Microsoft SQL Server](/integrations/libraries/mssql) page.

## Enable read-committed snapshot

SQL Server's default `READ COMMITTED` isolation takes shared read locks, so the daemon and the webserver block each other under load. Postgres does not behave this way, and neither does SQL Server once you run:

```sql
ALTER DATABASE dagster SET READ_COMMITTED_SNAPSHOT ON;
```

Dagster logs a warning at startup if this is off. It is left to whoever provisions the database: it is a database-wide setting, it needs elevated permissions, and it briefly requires exclusive access. Azure SQL Database has it on by default.

## Deadlocks are expected under load

SQL Server has no `INSERT ... ON CONFLICT`, so Dagster's upserts are `MERGE ... WITH (HOLDLOCK, UPDLOCK)`, which is serializable. At that isolation level SQL Server protects a key _range_ rather than a row, so two processes writing different rows can still be chosen as deadlock victims: two daemons sending heartbeats, or two runs materializing unrelated assets.

This is normal rather than a fault, and SQL Server's own error says what to do about it: rerun the transaction. `dagster-mssql` does, with jittered backoff. Deadlocks logged at DEBUG are routine; a `DagsterMSSQLException` naming the deadlock victim means the retries were exhausted, which is worth investigating.

## Collation does not matter

Dagster's text columns are `NVARCHAR` on SQL Server, so asset keys, partition keys and run tags containing non-ASCII characters round-trip correctly under any collation, including on SQL Server 2017 where UTF-8 collations are not available.

## Identifier columns are bounded

SQL Server cannot index `NVARCHAR(max)`, so columns that participate in an index key are bounded rather than unbounded: asset keys at 256 characters, partition and step keys at 128. Postgres has a comparable btree key limit, and MySQL indexes only a 64-character prefix of these same columns. A value over the bound is rejected rather than silently truncated.

## Schema migrations

`dagster-mssql` ships its own Alembic revision tree rather than sharing the one in `dagster` core, whose per-dialect branches emit DDL that is not valid on SQL Server. Run `dagster instance migrate` after upgrading Dagster, as with any other storage backend.

## Connection errors

Errors that reconnecting cannot fix, such as a rejected login or a missing permission, are raised immediately. Transient errors back off exponentially with jitter, which matters most on Azure SQL: a failover or a throttling event drops every Dagster process at once, and they should not all reconnect in lockstep.
