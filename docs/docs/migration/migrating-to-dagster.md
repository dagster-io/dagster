---
title: Migrating to Dagster
description: How to bring existing Python scripts, Airflow DAGs, and Prefect flows into Dagster.
last_update:
  author: Dennis Hume
sidebar_position: 10
---

If you have existing data pipelines—whether standalone Python scripts run by cron, Airflow DAGs, or Prefect flows—you can migrate them to Dagster incrementally.

## Incremental migration strategy

You don't need to migrate everything at once. A common approach:

1. **Run both systems in parallel.** Keep your existing scheduler running while you bring pipelines into Dagster one at a time. Dagster won't interfere with your existing cron jobs or Airflow instance.
2. **Migrate leaf pipelines first.** Start with pipelines that don't depend on upstream Airflow tasks—these have the fewest cross-system dependencies to manage.
3. **Use sensors for cross-system handoffs.** While migrating, a Dagster [`@sensor`](/guides/automate/sensors) can watch for files, database rows, or other signals produced by your old system and trigger Dagster runs. This lets the two systems cooperate without tight coupling.
4. **Cut over the schedule last.** Once the Dagster version is confirmed working, disable the old cron entry or Airflow DAG and activate the Dagster schedule.

## Migration guides

- [Airflow to Dagster](/migration/airflow-to-dagster) — Rewrite Airflow DAGs as native Dagster assets
- [Prefect to Dagster](/migration/prefect-to-dagster) — Convert Prefect flows and tasks to Dagster assets
- [Python to Dagster](/migration/python-to-dagster) — Wrap cron-scheduled scripts as Dagster assets

## Concept mapping reference

| Dagster                                                                         | Airflow                                    | Prefect                        |
| ------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------ |
| Asset graph                                                                     | DAG                                        | Flow                           |
| [`@asset`](/guides/build/assets/)                                               | `@task`                                    | `@task`                        |
| [`@schedule`](/guides/automate/schedules/) with `define_asset_job`              | `schedule` on `@dag`                       | Deployment schedule on `@flow` |
| `deps` for ordering; [I/O manager](/guides/build/io-managers/) for data handoff | XCom                                       | Task return values             |
| [`retry_policy`](/api/dagster/ops#dagster.RetryPolicy) on asset                 | `retries`, `retry_delay` in `default_args` | `retries` on `@task`           |
| `group_name`, `tags` on asset                                                   | DAG tags                                   | Flow tags                      |
| [Resources](/guides/build/external-resources/)                                  | Airflow Variables / Connections            | Prefect Blocks                 |
| [`@sensor`](/guides/automate/sensors)                                           | `ExternalTaskSensor`, `FileSensor`         | Prefect automations            |

## Common pitfalls

**`deps` is ordering, not data passing.** The most common mistake when migrating from Airflow or Prefect: expecting downstream assets to receive the upstream return value automatically. They don't. Either read inputs from your storage layer inside each asset, or use an [I/O manager](/guides/build/io-managers/) to handle the handoff.

**Connections and secrets need to become resources.** Airflow Connections and Prefect Blocks store credentials in their respective metadata backends. In Dagster, move these to [Resources](/guides/build/external-resources/). Resources are injected at runtime via function parameters and can be configured per-environment.

**Sensors replace polling operators.** `ExternalTaskSensor`, `FileSensor`, `HttpSensor`, and similar Airflow operators don't have direct op-level equivalents. Replace them with a Dagster [`@sensor`](/guides/automate/sensors) that polls for the condition and yields a `RunRequest`.

**Schedules don't backfill on deploy by default.** Airflow's `catchup=True` is the default; Dagster doesn't have a direct equivalent. If you need historical backfills, trigger them explicitly using [backfill](/guides/build/partitions-and-backfills/backfilling-data) rather than relying on deployment behavior.

**Scripts need explicit asset boundaries.** When migrating from cron-scheduled scripts, you'll need to decide what each asset represents. A single script may produce multiple logical outputs that benefit from being modeled as separate assets with their own materialization history and lineage.
