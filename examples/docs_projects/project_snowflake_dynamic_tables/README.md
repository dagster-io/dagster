# Snowflake Dynamic Tables as Virtual Assets

This example demonstrates how to represent Snowflake Dynamic Tables as **virtual assets** in Dagster using `AssetSpec(is_virtual=True)`.

## What This Shows

Snowflake Dynamic Tables are auto-refreshed by Snowflake — Dagster never needs to execute them. The correct way to represent them is as virtual assets:

- **External source tables** (`raw_orders`, `raw_customers`) — plain `AssetSpec`, loaded by an ETL pipeline
- **Snowflake Dynamic Tables** (`customer_lifetime_value`, `daily_revenue_rollup`) — `AssetSpec(is_virtual=True)`, Snowflake manages refresh
- **Downstream asset** (`executive_dashboard_report`) — `@asset` with `AutomationCondition.eager().resolve_through_virtual()`

### Why `is_virtual=True`?

Virtual assets are transparent in Dagster's execution graph. They represent transformations that exist outside Dagster's control (like Snowflake's auto-refresh). Unlike regular external assets, virtual assets can be "seen through" by automation conditions:

```
raw_orders ──> customer_lifetime_value (virtual) ──> executive_dashboard_report
                                                           ↑
                   eager() resolves through virtual: sees raw_orders
```

When `raw_orders` is materialized, `AutomationCondition.eager().resolve_through_virtual()` automatically requests a run for `executive_dashboard_report` — even though its direct upstream (the dynamic table) is virtual and never executed by Dagster.

This mirrors how dbt enables `enable_dbt_views_as_virtual_assets` for dbt view models.

### Contrast with the `snowflake_cortex` Example

The `snowflake_cortex` example represents dynamic tables as regular `@asset` functions returning `MaterializeResult`. That pattern is observable (you can "materialize" them to record metadata) but semantically incorrect — you'd be asking Dagster to execute something Snowflake manages.

`is_virtual=True` is the right model: the asset exists in the lineage graph, Dagster can monitor it via observations, but it's never in an execution plan.

## Setup

### Prerequisites

- Snowflake account with a warehouse
- Python 3.10+

### 1. Create the Snowflake Tables

Run [`sql/create_dynamic_tables.sql`](sql/create_dynamic_tables.sql) in your Snowflake environment (replace `<YOUR_WAREHOUSE>`).

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Snowflake credentials
```

### 3. Install and Run

```bash
uv sync
source .env  # or: export $(cat .env | xargs)
uv run dagster dev -m snowflake_dynamic_tables
```

Open http://localhost:3000 and explore the asset lineage.

## What to Observe in the UI

**Asset lineage graph:**

- `raw_orders` + `raw_customers` → `customer_lifetime_value` (virtual, snowflake badge) → `executive_dashboard_report`
- `raw_orders` → `daily_revenue_rollup` (virtual, snowflake badge) → `executive_dashboard_report`
- The virtual assets are shown in the graph but cannot be selected for materialization

**Automation behavior:**

1. Materialize `raw_orders` and `raw_customers` (or use "Report materialization" for the external sources)
2. Watch `executive_dashboard_report` get automatically requested (eager automation resolves through the virtual dynamic tables)

**Sensor observations:**

- The `dynamic_table_freshness_sensor` ticks every 60 seconds
- Each tick emits `AssetObservation` events for the virtual assets, updating their metadata timeline with freshness status from `information_schema.dynamic_tables`

## Running Tests

Unit tests require no Snowflake credentials:

```bash
uv run pytest tests/ -v
```

## Key Files

| File                            | Purpose                                                   |
| ------------------------------- | --------------------------------------------------------- |
| `assets/sources.py`             | External `AssetSpec` for raw data tables                  |
| `assets/dynamic_tables.py`      | `AssetSpec(is_virtual=True)` for Snowflake Dynamic Tables |
| `assets/analytics.py`           | `@asset` with `resolve_through_virtual()` automation      |
| `sensors.py`                    | Freshness sensor emitting `AssetObservation` events       |
| `sql/create_dynamic_tables.sql` | DDL to set up Snowflake tables                            |
