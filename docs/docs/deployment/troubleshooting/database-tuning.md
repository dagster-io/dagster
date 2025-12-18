---
title: Database tuning
sidebar_position: 500
description: TK
---

TK - intro

## Step 1: Run Dagster database clean-up job

This Dagster database clean-up job can be run daily. Note that you should test it on a single run first.

The clean-up job does two things:

- Deletes DEBUG logs older than one week, and INFO/WARNING logs older than two months.
- Deletes unimportant event_logs one month after they were created.

### Step 1.1: Run Python script

```python
from textwrap import dedent

from dagster import Config, OpExecutionContext, ResourceParam, in_process_executor, job, op
from pydantic import Field
from sqlalchemy import Engine, text


class DagsterCleanupDebugLogsConfig(Config):
    delete_after_days: int = Field(7, description="Number of days to keep DEBUG event logs")


@op
def dagster_cleanup_debug_logs(
    context: OpExecutionContext, postgresql_dagster_engine: ResourceParam[Engine], config: DagsterCleanupDebugLogsConfig
):
    # Run in transaction
    with postgresql_dagster_engine.begin() as conn:
        result = conn.execute(
            text(
                dedent(
                    """\
                    DELETE
                    FROM event_logs el
                    WHERE
                        dagster_event_type IS NULL
                        AND event::jsonb->>'level' = '10'
                        AND timestamp < CURRENT_DATE - MAKE_INTERVAL(days => :delete_after_days)
                """
                )
            ),
            parameters={"delete_after_days": config.delete_after_days},
        )
    context.log.info(f"Deleted {result.rowcount} debug logs older than {config.delete_after_days} days!")


class DagsterCleanupInfoLogsConfig(Config):
    delete_after_days: int = Field(60, description="Number of days to keep INFO event logs")


@op
def dagster_cleanup_info_logs(
    context: OpExecutionContext, postgresql_dagster_engine: ResourceParam[Engine], config: DagsterCleanupInfoLogsConfig
):
    # Run in transaction
    with postgresql_dagster_engine.begin() as conn:
        result = conn.execute(
            text(
                dedent(
                    """\
                    DELETE
                    FROM event_logs el
                    WHERE
                        dagster_event_type IS NULL
                        AND event::jsonb->>'level' = '20'
                        AND timestamp < CURRENT_DATE - MAKE_INTERVAL(days => :delete_after_days)
                """
                )
            ),
            parameters={"delete_after_days": config.delete_after_days},
        )
    context.log.info(f"Deleted {result.rowcount} info logs older than {config.delete_after_days} days!")


class DagsterCleanupWarningLogsConfig(Config):
    delete_after_days: int = Field(60, description="Number of days to keep WARNING event logs")


@op
def dagster_cleanup_warning_logs(
    context: OpExecutionContext,
    postgresql_dagster_engine: ResourceParam[Engine],
    config: DagsterCleanupWarningLogsConfig,
):
    # Run in transaction
    with postgresql_dagster_engine.begin() as conn:
        result = conn.execute(
            text(
                dedent(
                    """\
                    DELETE
                    FROM event_logs el
                    WHERE
                        dagster_event_type IS NULL
                        AND event::jsonb->>'level' = '30'
                        AND timestamp < CURRENT_DATE - MAKE_INTERVAL(days => :delete_after_days)
                """
                )
            ),
            parameters={"delete_after_days": config.delete_after_days},
        )
    context.log.info(f"Deleted {result.rowcount} warning logs older than {config.delete_after_days} days!")


class DagsterCleanupUnimportantEventsConfig(Config):
    delete_after_days: int = Field(30, description="Number of days to keep transitory/unimportant event logs")


@op
def dagster_cleanup_unimportant_events(
    context: OpExecutionContext,
    postgresql_dagster_engine: ResourceParam[Engine],
    config: DagsterCleanupUnimportantEventsConfig,
):
    # Run in transaction
    with postgresql_dagster_engine.begin() as conn:
        result = conn.execute(
            text(
                dedent(
                    """\
                    DELETE
                    FROM event_logs
                    WHERE
                        timestamp < CURRENT_DATE - MAKE_INTERVAL(days => :delete_after_days)
                            AND dagster_event_type IN (
                                -- Transition states. Used in business logic, but not important after the job finishes.
                                'ASSET_MATERIALIZATION_PLANNED',
                                -- System logs
                                'ENGINE_EVENT',
                                'HANDLED_OUTPUT',
                                'LOADED_INPUT',
                                -- Transition states. Used in business logic, but not important after the job finishes.
                                'PIPELINE_CANCELING',
                                'PIPELINE_ENQUEUED',
                                'PIPELINE_STARTING',
                                -- System logs
                                'RESOURCE_INIT_FAILURE',
                                'RESOURCE_INIT_STARTED',
                                'RESOURCE_INIT_SUCCESS',
                                'STEP_INPUT',
                                'STEP_OUTPUT',
                                'STEP_WORKER_STARTED',
                                'STEP_WORKER_STARTING'
                            )
                    """
                )
            ),
            parameters={"delete_after_days": config.delete_after_days},
        )
    context.log.info(f"Deleted {result.rowcount} unimportant events older than {config.delete_after_days} days!")


@job(
    description="Cleans up Dagster Postgres database. See op descriptions for details.",
    executor_def=in_process_executor,
)
def dagster_cleanup_job():
    dagster_cleanup_debug_logs()
    dagster_cleanup_info_logs()
    dagster_cleanup_warning_logs()
    dagster_cleanup_unimportant_events()
```

### Step 1.2: Create additional indexes

```sql
CREATE INDEX CONCURRENTLY idx_clear_event_logs_user_logs
	ON event_logs ((event::jsonb ->> 'level'::text), timestamp)
	WHERE (dagster_event_type IS NULL);

CREATE INDEX CONCURRENTLY idx_clear_event_logs_system_events
	ON event_logs (dagster_event_type, timestamp)
	WHERE (dagster_event_type IS NOT NULL);
```

### What to expect when running clean-up

- This clean-up job can run up to several hours (without indexes) or a few minutes (with indexes) depending on your database size, I/O speed.
- Both indexes are relatively small compared to the `event_logs` table size, so I highly recommend creating them.
- 🚨 **When any row gets inserted/updated/deleted, the information is saved to transaction log, so the disk size will temporarily increase! In case of our database (event_logs size = 370GB), the transaction log increased to 60GB! When your disk runs out of space, your DB will change to ReadOnly and dagster will stop running (I learned the hard way). So if you are reading this, because your got Grafana alert telling you that Dagster DB is running out of space, please scale it up beforehand.**

### What to expect after the clean-up job completes

- You will see higher CPU/IO for few hours as the transaction logs get applied.
- ⚠️ You will see DISK USAGE going back **TO WHERE IT WAS, BUT NOT LOWER** as transaction logs get applied.
- Deleted rows were only marked as DEAD ROWS and not deleted yet. 
- You need to run VACUUM to let postgres reuse them for new inserts.

## Step 2: Run VACUUM to let postgres reuse rows marked for deletion

### Utility queries for VACUUM

```sql
-- Get dead tuples: deleted/updated rows that were not collected yet
SELECT relname, n_dead_tup FROM pg_stat_user_tables ORDER BY n_dead_tup DESC;

-- Get analyze stats
SELECT relname, last_vacuum, last_analyze, last_autovacuum, last_autoanalyze,  vacuum_count, autovacuum_count, analyze_count, autoanalyze_count
FROM pg_stat_all_tables 
WHERE relname = 'event_logs'

-- Table/Index size
SELECT relname, pg_size_pretty(pg_relation_size(oid)) AS table_size,
       pg_size_pretty(pg_total_relation_size(oid) - pg_relation_size(oid)) AS index_size
FROM pg_class
WHERE relname = 'event_logs'

-- Run vacuum + refresh indexes
VACUUM VERBOSE ANALYZE dagster.event_logs

-- Vacuum progress
SELECT 
    n.nspname || '.' || c.relname AS table_name,
    v.phase,
    round(100.0 * v.heap_blks_scanned / NULLIF(v.heap_blks_total, 0), 2) AS pct_scanned,
    round(100.0 * v.heap_blks_vacuumed / NULLIF(v.heap_blks_total, 0), 2) AS pct_vacuumed,
    v.heap_blks_total,
    v.heap_blks_scanned,
    v.heap_blks_vacuumed
FROM 
    pg_stat_progress_vacuum v
JOIN 
    pg_class c ON v.relid = c.oid
JOIN 
    pg_namespace n ON c.relnamespace = n.oid;
```

### Details about VACUUM (RECOVERING DISK SPACE)

https://www.postgresql.org/docs/current/routine-vacuuming.html#VACUUM-FOR-SPACE-RECOVERY

The standard form of VACUUM removes dead row versions in tables and indexes and marks the space available for future reuse. **However, it will not return the space to the operating system**, except in the special case where one or more pages at the end of a table become entirely free and an exclusive table lock can be easily obtained. In contrast, VACUUM FULL actively **compacts tables by writing a complete new version of the table file with no dead space**. This minimizes the size of the table, but can take a long time. **It also requires extra disk space for the new copy of the table, until the operation completes.**

The usual goal of routine vacuuming is to do standard VACUUMs often enough to avoid needing VACUUM FULL. The autovacuum daemon attempts to work this way, and in fact will never issue VACUUM FULL. In this approach, t**he idea is not to keep tables at their minimum size, but to maintain steady-state usage of disk space: each table occupies space equivalent to its minimum size plus however much space gets used up between vacuum runs. Although VACUUM FULL can be used to shrink a table back to its minimum size and return the disk space to the operating system, there is not much point in this if the table will just grow again in the future.** Thus, moderately-frequent standard VACUUM runs are a better approach than infrequent VACUUM FULL runs for maintaining heavily-updated tables.

## Step 3: Shrink the datbase with `pg_repack`

- I was able to run pg_repack on the whole database and cut the overall disk usage by half!
- There was no downtime and the whole process took ~2,5h with under-utilized database.

```sql
SELECT
    relname AS table_name,
    pg_size_pretty(pg_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))) AS table_size,
    pg_size_pretty(pg_indexes_size(quote_ident(schemaname) || '.' || quote_ident(relname))) AS indexes_size,
    pg_size_pretty(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(relname))) AS total_size
FROM 
    pg_stat_user_tables
WHERE 
    schemaname = 'dagster'
ORDER BY 
    table_name

>

table_name                    |table_size|indexes_size|total_size|  Before / After  |table_size|indexes_size|total_size|
------------------------------+----------+------------+----------+                  +----------+------------+----------+
alembic_version               |8192 bytes|16 kB       |56 kB     |                  |8192 bytes|16 kB       |24 kB     |
asset_check_executions        |0 bytes   |24 kB       |32 kB     |                  |0 bytes   |24 kB       |32 kB     |
asset_daemon_asset_evaluations|4056 kB   |1480 kB     |37 MB     |                  |2920 kB   |632 kB      |29 MB     |
asset_event_tags              |2361 MB   |2359 MB     |4721 MB   |                  |2268 MB   |1888 MB     |4157 MB   |
asset_keys                    |24 MB     |608 kB      |37 MB     |                  |3408 kB   |208 kB      |10 MB     |
backfill_tags                 |208 kB    |160 kB      |408 kB    |                  |192 kB    |160 kB      |384 kB    |
bulk_actions                  |6848 kB   |752 kB      |12 MB     |                  |4704 kB   |480 kB      |7488 kB   |
concurrency_limits            |0 bytes   |16 kB       |24 kB     |                  |0 bytes   |16 kB       |24 kB     |
concurrency_slots             |0 bytes   |16 kB       |40 kB     |                  |0 bytes   |8192 bytes  |16 kB     |
daemon_heartbeats             |2152 kB   |80 kB       |2392 kB   |                  |56 kB     |32 kB       |128 kB    |
dynamic_partitions            |1112 kB   |1184 kB     |2336 kB   |                  |1080 kB   |1056 kB     |2168 kB   |
event_logs                    |137 GB    |31 GB       |169 GB    |        !         |44 GB     |5986 MB     |51 GB     |
instance_info                 |8192 bytes|16 kB       |64 kB     |                  |8192 bytes|16 kB       |32 kB     |
instigators                   |22 MB     |560 kB      |29 MB     |                  |776 kB    |104 kB      |1632 kB   |
job_ticks                     |446 MB    |83 MB       |633 MB    |                  |446 MB    |83 MB       |633 MB    |
jobs                          |23 MB     |568 kB      |29 MB     |                  |808 kB    |104 kB      |1680 kB   |
kvs                           |1384 kB   |32 kB       |1456 kB   |                  |32 kB     |32 kB       |104 kB    |
pending_steps                 |0 bytes   |16 kB       |24 kB     |                  |0 bytes   |16 kB       |24 kB     |
run_tags                      |4114 MB   |8488 MB     |12 GB     |                  |4052 MB   |6740 MB     |11 GB     |
runs                          |4899 MB   |1199 MB     |7535 MB   |                  |4562 MB   |685 MB      |6516 MB   |
secondary_indexes             |8192 bytes|32 kB       |80 kB     |                  |8192 bytes|32 kB       |48 kB     |
snapshots                     |231 MB    |29 MB       |400 MB    |                  |216 MB    |23 MB       |379 MB    |
```

Since we are using [Azure Psqlflex instance](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/service-overview) instance, some parts might different, but I will share my path. 

0. [Original guide by Azure](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-perform-fullvacuum-pg-repack)
1. Enable pg_repack in Azure UI (under azure.extensions) [LINK](https://learn.microsoft.com/en-us/azure/postgresql/extensions/how-to-allow-extensions?tabs=allow-extensions-portal#allow-extensions)
2. Install `pg_repack` client (the one that matching your postgres version)

    ```shell
    brew install postgresql@14 pqxn
    pgxn install pg_repack==1.4.7
    ```
3. Add permissions for dagster schema to admin user you run the pg_repack with

    ```sql
    GRANT dagster to my_admin
    ```
4. Test `pg_repack` command with dry run

    ```shell
    /opt/homebrew/Cellar/postgresql@14/14.17_1/bin/pg_repack --host=my-database.postgres.database.azure.com --username=my_admin --dbname=dagster --schema=dagster --jobs=2 --no-kill-backend --no-superuser-check --dry-run
    INFO: Dry run enabled, not executing repack
    Password:
    NOTICE: Setting up workers.conns
    INFO: repacking table "dagster.alembic_version"
    INFO: repacking table "dagster.asset_check_executions"
    INFO: repacking table "dagster.asset_daemon_asset_evaluations"
    INFO: repacking table "dagster.asset_event_tags"
    INFO: repacking table "dagster.asset_keys"
    INFO: repacking table "dagster.backfill_tags"
    INFO: repacking table "dagster.bulk_actions"
    INFO: repacking table "dagster.concurrency_limits"
    INFO: repacking table "dagster.concurrency_slots"
    INFO: repacking table "dagster.daemon_heartbeats"
    INFO: repacking table "dagster.dynamic_partitions"
    INFO: repacking table "dagster.event_logs"
    INFO: repacking table "dagster.instance_info"
    INFO: repacking table "dagster.instigators"
    INFO: repacking table "dagster.jobs"
    INFO: repacking table "dagster.job_ticks"
    INFO: repacking table "dagster.kvs"
    INFO: repacking table "dagster.pending_steps"
    INFO: repacking table "dagster.runs"
    INFO: repacking table "dagster.run_tags"
    INFO: repacking table "dagster.secondary_indexes"
    INFO: repacking table "dagster.snapshots"
    ```
5. Run `pg_repack` command

    ```shell
    /opt/homebrew/Cellar/postgresql@14/14.17_1/bin/pg_repack --host=my-database.postgres.database.azure.com --username=my_admin --dbname=dagster --schema=dagster --jobs=2 --no-kill-backend --no-superuser-check
    Password:
    NOTICE: Setting up workers.conns
    INFO: repacking table "dagster.alembic_version"
    INFO: repacking table "dagster.asset_check_executions"
    ```

    ```shell
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_4085990 ON repack.table_4085983 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE INDEX index_4085992 ON repack.table_4085983 USING btree (asset_key, check_name, materialization_event_storage_id, partition)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_4085990 ON repack.table_4085983 USING btree (id)
    LOG: Assigning worker 0 to build index #2: CREATE UNIQUE INDEX index_4085993 ON repack.table_4085983 USING btree (asset_key, check_name, run_id, partition)
    LOG: Command finished in worker 1: CREATE INDEX index_4085992 ON repack.table_4085983 USING btree (asset_key, check_name, materialization_event_storage_id, partition)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_4085993 ON repack.table_4085983 USING btree (asset_key, check_name, run_id, partition)
    INFO: repacking table "dagster.asset_daemon_asset_evaluations"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_484858 ON repack.table_484850 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_484861 ON repack.table_484850 USING btree (asset_key, evaluation_id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_484858 ON repack.table_484850 USING btree (id)
    LOG: Assigning worker 0 to build index #2: CREATE INDEX index_484860 ON repack.table_484850 USING btree (evaluation_id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_484861 ON repack.table_484850 USING btree (asset_key, evaluation_id)
    LOG: Command finished in worker 0: CREATE INDEX index_484860 ON repack.table_484850 USING btree (evaluation_id)
    INFO: repacking table "dagster.asset_event_tags"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_25020 ON repack.table_25013 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE INDEX index_25027 ON repack.table_25013 USING btree (asset_key, key, value)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_25020 ON repack.table_25013 USING btree (id)
    LOG: Assigning worker 0 to build index #2: CREATE INDEX index_25028 ON repack.table_25013 USING btree (event_id)
    LOG: Command finished in worker 0: CREATE INDEX index_25028 ON repack.table_25013 USING btree (event_id)
    LOG: Command finished in worker 1: CREATE INDEX index_25027 ON repack.table_25013 USING btree (asset_key, key, value)
    INFO: repacking table "dagster.asset_keys"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_24996 ON repack.table_24986 USING btree (asset_key)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_24994 ON repack.table_24986 USING btree (id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_24994 ON repack.table_24986 USING btree (id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_24996 ON repack.table_24986 USING btree (asset_key)
    INFO: repacking table "dagster.backfill_tags"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_4415514 ON repack.table_4415508 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE INDEX index_4415516 ON repack.table_4415508 USING btree (backfill_id, id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_4415514 ON repack.table_4415508 USING btree (id)
    LOG: Command finished in worker 1: CREATE INDEX index_4415516 ON repack.table_4415508 USING btree (backfill_id, id)
    INFO: repacking table "dagster.bulk_actions"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_24903 ON repack.table_24894 USING btree (key)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_24901 ON repack.table_24894 USING btree (id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_24901 ON repack.table_24894 USING btree (id)
    LOG: Assigning worker 1 to build index #2: CREATE INDEX index_24907 ON repack.table_24894 USING btree (key)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_24903 ON repack.table_24894 USING btree (key)
    LOG: Assigning worker 0 to build index #3: CREATE INDEX index_24906 ON repack.table_24894 USING btree (action_type)
    LOG: Command finished in worker 1: CREATE INDEX index_24907 ON repack.table_24894 USING btree (key)
    LOG: Assigning worker 1 to build index #4: CREATE INDEX index_24905 ON repack.table_24894 USING btree (selector_id)
    LOG: Command finished in worker 0: CREATE INDEX index_24906 ON repack.table_24894 USING btree (action_type)
    LOG: Assigning worker 0 to build index #5: CREATE INDEX index_24908 ON repack.table_24894 USING btree (status)
    LOG: Command finished in worker 1: CREATE INDEX index_24905 ON repack.table_24894 USING btree (selector_id)
    LOG: Command finished in worker 0: CREATE INDEX index_24908 ON repack.table_24894 USING btree (status)
    INFO: repacking table "dagster.concurrency_limits"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_4086003 ON repack.table_4085995 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_4086005 ON repack.table_4085995 USING btree (concurrency_key)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_4086003 ON repack.table_4085995 USING btree (id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_4086005 ON repack.table_4085995 USING btree (concurrency_key)
    INFO: repacking table "dagster.concurrency_slots"
    INFO: repacking table "dagster.daemon_heartbeats"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_24890 ON repack.table_24884 USING btree (daemon_type)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_484846 ON repack.table_24884 USING btree (id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_484846 ON repack.table_24884 USING btree (id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_24890 ON repack.table_24884 USING btree (daemon_type)
    INFO: repacking table "dagster.dynamic_partitions"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_25008 ON repack.table_25000 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_25010 ON repack.table_25000 USING btree (partitions_def_name, partition)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_25008 ON repack.table_25000 USING btree (id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_25010 ON repack.table_25000 USING btree (partitions_def_name, partition)
    INFO: repacking table "dagster.event_logs"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_24977 ON repack.table_24970 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE INDEX index_24979 ON repack.table_24970 USING btree (dagster_event_type, id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_24977 ON repack.table_24970 USING btree (id)
    LOG: Assigning worker 0 to build index #2: CREATE INDEX index_24982 ON repack.table_24970 USING btree (asset_key, dagster_event_type, id) WHERE (asset_key IS NOT NULL)
    LOG: Command finished in worker 1: CREATE INDEX index_24979 ON repack.table_24970 USING btree (dagster_event_type, id)
    LOG: Assigning worker 1 to build index #3: CREATE INDEX index_24983 ON repack.table_24970 USING btree (asset_key, dagster_event_type, partition, id) WHERE ((asset_key IS NOT NULL) AND (partition IS NOT NULL))
    LOG: Command finished in worker 0: CREATE INDEX index_24982 ON repack.table_24970 USING btree (asset_key, dagster_event_type, id) WHERE (asset_key IS NOT NULL)
    LOG: Assigning worker 0 to build index #4: CREATE INDEX index_24981 ON repack.table_24970 USING btree (run_id, id)
    LOG: Command finished in worker 1: CREATE INDEX index_24983 ON repack.table_24970 USING btree (asset_key, dagster_event_type, partition, id) WHERE ((asset_key IS NOT NULL) AND (partition IS NOT NULL))
    LOG: Assigning worker 1 to build index #5: CREATE INDEX index_24980 ON repack.table_24970 USING btree (step_key)
    LOG: Command finished in worker 1: CREATE INDEX index_24980 ON repack.table_24970 USING btree (step_key)
    LOG: Command finished in worker 0: CREATE INDEX index_24981 ON repack.table_24970 USING btree (run_id, id)
    INFO: repacking table "dagster.instance_info"
    INFO: repacking table "dagster.instigators"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_25056 ON repack.table_25047 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_25058 ON repack.table_25047 USING btree (selector_id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_25056 ON repack.table_25047 USING btree (id)
    LOG: Assigning worker 0 to build index #2: CREATE INDEX index_25060 ON repack.table_25047 USING btree (instigator_type)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_25058 ON repack.table_25047 USING btree (selector_id)
    LOG: Command finished in worker 0: CREATE INDEX index_25060 ON repack.table_25047 USING btree (instigator_type)
    INFO: repacking table "dagster.jobs"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_25042 ON repack.table_25031 USING btree (job_origin_id)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_25040 ON repack.table_25031 USING btree (id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_25040 ON repack.table_25031 USING btree (id)
    LOG: Assigning worker 1 to build index #2: CREATE INDEX index_25044 ON repack.table_25031 USING btree (job_type)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_25042 ON repack.table_25031 USING btree (job_origin_id)
    LOG: Command finished in worker 1: CREATE INDEX index_25044 ON repack.table_25031 USING btree (job_type)
    INFO: repacking table "dagster.job_ticks"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_25072 ON repack.table_25063 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE INDEX index_25076 ON repack.table_25063 USING btree (job_origin_id, status)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_25072 ON repack.table_25063 USING btree (id)
    LOG: Assigning worker 0 to build index #2: CREATE INDEX index_25077 ON repack.table_25063 USING btree (job_origin_id, "timestamp")
    LOG: Command finished in worker 1: CREATE INDEX index_25076 ON repack.table_25063 USING btree (job_origin_id, status)
    LOG: Assigning worker 1 to build index #3: CREATE INDEX index_25075 ON repack.table_25063 USING btree (selector_id, "timestamp")
    LOG: Command finished in worker 0: CREATE INDEX index_25077 ON repack.table_25063 USING btree (job_origin_id, "timestamp")
    LOG: Assigning worker 0 to build index #4: CREATE INDEX index_25074 ON repack.table_25063 USING btree (job_origin_id)
    LOG: Command finished in worker 1: CREATE INDEX index_25075 ON repack.table_25063 USING btree (selector_id, "timestamp")
    LOG: Command finished in worker 0: CREATE INDEX index_25074 ON repack.table_25063 USING btree (job_origin_id)
    INFO: repacking table "dagster.kvs"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_484842 ON repack.table_24915 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_24921 ON repack.table_24915 USING btree (key)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_24921 ON repack.table_24915 USING btree (key)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_484842 ON repack.table_24915 USING btree (id)
    INFO: repacking table "dagster.pending_steps"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_484884 ON repack.table_484876 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_484886 ON repack.table_484876 USING btree (concurrency_key, run_id, step_key)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_484884 ON repack.table_484876 USING btree (id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_484886 ON repack.table_484876 USING btree (concurrency_key, run_id, step_key)
    INFO: repacking table "dagster.runs"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_24933 ON repack.table_24924 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_24935 ON repack.table_24924 USING btree (run_id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_24933 ON repack.table_24924 USING btree (id)
    LOG: Assigning worker 0 to build index #2: CREATE INDEX index_24944 ON repack.table_24924 USING btree (partition_set, partition)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_24935 ON repack.table_24924 USING btree (run_id)
    LOG: Assigning worker 1 to build index #3: CREATE INDEX index_24943 ON repack.table_24924 USING btree (status, update_timestamp, create_timestamp)
    LOG: Command finished in worker 0: CREATE INDEX index_24944 ON repack.table_24924 USING btree (partition_set, partition)
    LOG: Assigning worker 0 to build index #4: CREATE INDEX index_24942 ON repack.table_24924 USING btree (status)
    LOG: Command finished in worker 1: CREATE INDEX index_24943 ON repack.table_24924 USING btree (status, update_timestamp, create_timestamp)
    LOG: Assigning worker 1 to build index #5: CREATE INDEX index_24945 ON repack.table_24924 USING btree (pipeline_name, id)
    LOG: Command finished in worker 0: CREATE INDEX index_24942 ON repack.table_24924 USING btree (status)
    LOG: Assigning worker 0 to build index #6: CREATE INDEX index_4415487 ON repack.table_24924 USING btree (backfill_id, id)
    LOG: Command finished in worker 1: CREATE INDEX index_24945 ON repack.table_24924 USING btree (pipeline_name, id)
    LOG: Command finished in worker 0: CREATE INDEX index_4415487 ON repack.table_24924 USING btree (backfill_id, id)
    INFO: repacking table "dagster.run_tags"
    WARNING: skipping invalid index: CREATE UNIQUE INDEX idx_run_tags_run_id ON dagster.run_tags USING btree (key, value, run_id)
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_24955 ON repack.table_24948 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE INDEX index_4086007 ON repack.table_24948 USING btree (run_id, id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_24955 ON repack.table_24948 USING btree (id)
    LOG: Assigning worker 0 to build index #2: CREATE INDEX index_4450048 ON repack.table_24948 USING btree (key, value, run_id)
    LOG: Command finished in worker 1: CREATE INDEX index_4086007 ON repack.table_24948 USING btree (run_id, id)
    LOG: Command finished in worker 0: CREATE INDEX index_4450048 ON repack.table_24948 USING btree (key, value, run_id)
    INFO: repacking table "dagster.secondary_indexes"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_24869 ON repack.table_24859 USING btree (name)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_24867 ON repack.table_24859 USING btree (id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_24867 ON repack.table_24859 USING btree (id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_24869 ON repack.table_24859 USING btree (name)
    INFO: repacking table "dagster.snapshots"
    LOG: Initial worker 0 to build index: CREATE UNIQUE INDEX index_24880 ON repack.table_24873 USING btree (id)
    LOG: Initial worker 1 to build index: CREATE UNIQUE INDEX index_24882 ON repack.table_24873 USING btree (snapshot_id)
    LOG: Command finished in worker 0: CREATE UNIQUE INDEX index_24880 ON repack.table_24873 USING btree (id)
    LOG: Command finished in worker 1: CREATE UNIQUE INDEX index_24882 ON repack.table_24873 USING btree (snapshot_id)
    ```

## Resources

- [PostgresQL Europe: Managing your Tuple Graveyard - Chelsea Dole](https://youtu.be/aW94NwTACBM). Very educative!
- After running **VACUUM** on `event_logs` table, it will stop growing in size as the space from deleted rows will get reused for new inserts.
- To visibly reduce disk size, you need to run **VACUUM FULL** (🚨 needs EXCLUSIVE LOCK => Downtime). Also needs extra space to create copy of shrunk table, so you need to upscale the disk first.
- [pg_repack](https://reorg.github.io/pg_repack/) or [pg_sqeeze](https://www.cybertec-postgresql.com/en/products/pg_squeeze/) act like VACUUM FULL, but with less EXCLUSIVE LOCKS (which are blocking). 
- [Using pg_squeeze](https://www.enterprisedb.com/docs/pg_extensions/pg_squeeze/using/#disk-space-requirements)
