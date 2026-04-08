---
title: Multi-workspace Databricks
description: Orchestrate data pipelines across multiple Databricks workspaces with Kafka ingestion and Fivetran SaaS integrations
last_update:
  author: Dagster Labs
sidebar_custom_props:
  logo: images/integrations/databricks.svg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/multi-workspace-databricks'
slug: '/examples/full-pipelines/multi-workspace-databricks'
---

In this example, you'll explore a Dagster project that demonstrates an enterprise data mesh architecture. The project shows how a single Dagster deployment can orchestrate data pipelines across multiple Databricks workspaces while integrating Kafka for real-time event ingestion and Fivetran for SaaS data syncs.

The core challenge this project addresses is common in large organizations: data is distributed across many systems — event streams, SaaS tools, legacy databases, and business-unit-specific Databricks workspaces — but the organization needs unified lineage tracking, consistent scheduling, and cross-domain analytics. Dagster acts as the control plane, maintaining a single asset graph that spans all of these systems.

The pipeline:

- Ingests real-time ERP and CRM events from Kafka topics
- Syncs SaaS data from Salesforce and HubSpot via Fivetran
- Accesses legacy SQL Server and PostgreSQL databases through Databricks Unity Catalog Lakehouse Federation
- Runs workspace-specific Databricks jobs across four business domains (customer analytics, sales analytics, finance reporting, and marketing attribution)
- Tracks full asset lineage from raw sources through workspace-specific transformations to cross-domain analytics

## Prerequisites

To follow the steps in this guide, you'll need:

- Python 3.10+ and [`uv`](https://docs.astral.sh/uv) installed. For more information, see the [Installation guide](/getting-started/installation).
- Familiarity with Python and asset-based pipelines.
- Active Databricks workspaces with job IDs and access tokens.
- A Kafka broker reachable from your Dagster deployment.

## Step 1: Set up your Dagster environment

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_multi_workspace_databricks
   ```

2. Install the required dependencies with `uv`:

   ```bash
   uv sync
   ```

3. Activate the virtual environment:

   <Tabs>
     <TabItem value="macos" label="MacOS/Unix">
       ```source .venv/bin/activate```
     </TabItem>
     <TabItem value="windows" label="Windows">
       ```.venv\Scripts\activate```
     </TabItem>
   </Tabs>

4. Configure credentials for your Databricks workspaces and Kafka broker (see [Configuration](#configuration) below).

## Step 2: Launch the Dagster webserver

Start the Dagster webserver from the project root:

```bash
dg dev
```

Open http://localhost:3000 in your browser. You'll see 21 assets across seven groups — the full data mesh from raw ingestion through analytics.

## Understanding the asset model

A key design choice in this project is that many assets have `pass` bodies rather than executing computation directly. This is intentional and reflects a fundamental Dagster pattern: **an asset represents data that exists somewhere, not necessarily computation that runs inside Dagster.**

The project has two categories of assets:

**External-system assets** are <PyObject section="assets" module="dagster" object="asset" decorator /> functions with empty bodies. They appear in the lineage graph so other assets can declare dependencies on them, but the actual data production happens outside Dagster:

- `raw_erp_events` and `raw_crm_events` are materialized by Kafka sensors, not by running the asset function directly. The sensor detects new messages, batches them, and triggers a run that marks the asset as materialized.
- `salesforce_data` and `hubspot_data` represent Fivetran connector syncs. Fivetran manages the sync schedule; Dagster tracks that these assets exist and what depends on them.
- `legacy_customer_data` and `legacy_transaction_data` represent tables accessed via Databricks Unity Catalog Lakehouse Federation. The data lives in on-premise SQL Server and PostgreSQL — Dagster provides lineage tracking for downstream consumers.

**Orchestrated assets** — the four workspace groups — are fully implemented by the [`DatabricksJobOrchestrator`](#the-databricksjoborchestrator-component) component. When materialized, they run a real Databricks job in the configured workspace and emit `MaterializeResult` for each asset produced.

This hybrid approach gives you complete lineage — from raw Kafka events through workspace transformations to cross-domain analytics — while letting each system own its own execution.

## Architecture

The project is organized into two layers:

### Core assets (`defs/core_assets/`)

Defined as standard `@asset` functions, these represent the shared data foundation:

| Group            | Assets                                                                                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `ingestion`      | `raw_erp_events`, `raw_crm_events`, `salesforce_data`, `hubspot_data`, `legacy_customer_data`, `legacy_transaction_data` |
| `transformation` | `enriched_customer_profiles`, `order_fulfillment_status`                                                                 |
| `analytics`      | `customer_360_view`, `marketing_attribution`                                                                             |

### Workspace assets (`defs/*/defs.yaml`)

Each of the four business domains is configured via a `defs.yaml` file using the reusable [`DatabricksJobOrchestrator`](#the-databricksjoborchestrator-component) component:

| Workspace               | Databricks job | Assets produced                                                                                       |
| ----------------------- | -------------- | ----------------------------------------------------------------------------------------------------- |
| `customer_analytics`    | Job 12345      | `enriched_profiles`, `customer_segments`                                                              |
| `sales_analytics`       | Job 12346      | `order_fulfillment`, `revenue_forecasting`                                                            |
| `finance_reporting`     | Job 12347      | `invoice_reconciliation`, `payment_tracking`, `financial_statements`, `customer_segments_aggregation` |
| `marketing_attribution` | Job 12348      | `campaign_performance`, `attribution_model`, `customer_lifetime_value`                                |

Data flows from the core ingestion assets (Kafka, Fivetran, legacy databases) into workspace-specific Databricks jobs, which produce domain-specific assets. Those workspace assets are then consumed by the `transformation` and `analytics` core assets to produce the final cross-domain outputs (`customer_360_view`, `marketing_attribution`).

## Kafka ingestion

Real-time ERP and CRM events flow through Kafka. Rather than polling Kafka on a fixed schedule from inside an asset, the project uses a sensor-driven pattern that maps naturally to event-driven ingestion.

### The KafkaResource

A <PyObject section="resources" module="dagster" object="ConfigurableResource" /> wraps the Kafka connection and is injected into sensors at runtime:

<CodeExample
  path="docs_projects/project_multi_workspace_databricks/src/project_multi_workspace_databricks/sensors.py"
  language="python"
  startAfter="start_kafka_resource"
  endBefore="end_kafka_resource"
  title="sensors.py — KafkaResource"
/>

The resource is registered in `defs/core_assets/__init__.py` with a default configuration pointing at `localhost:9092`. Update `bootstrap_servers` and `topics` for your deployment.

### The Kafka sensor

`kafka_sensor_factory` is a factory function that creates a <PyObject section="schedules-sensors" module="dagster" object="SensorDefinition" /> for a given replica ID and target asset key. Running two sensor instances (replica 0 for ERP, replica 1 for CRM) allows the project to consume from both topics in parallel without coordination:

<CodeExample
  path="docs_projects/project_multi_workspace_databricks/src/project_multi_workspace_databricks/sensors.py"
  language="python"
  startAfter="start_sensor_body"
  endBefore="end_sensor_body"
  title="sensors.py — sensor body"
/>

Each sensor tick:

1. Opens a Kafka consumer using the `KafkaResource`
2. Polls for up to 30 seconds, collecting a batch of up to 50 messages
3. If messages were received, yields a <PyObject section="schedules-sensors" module="dagster" object="RunRequest" /> with the batch serialized into run config
4. Commits Kafka offsets only after the run request is yielded successfully

The `run_key` is set to `max_offset_{n}`, which means Dagster deduplicates runs — if the sensor ticks before the previous run completes, a new `RunRequest` with the same offset won't trigger a duplicate run.

### Kafka asset definitions

The `raw_erp_events` and `raw_crm_events` assets themselves have `pass` bodies because the Kafka sensor — not the asset function — is what processes and materializes the data:

<CodeExample
  path="docs_projects/project_multi_workspace_databricks/src/project_multi_workspace_databricks/assets.py"
  language="python"
  startAfter="start_kafka_assets"
  endBefore="end_kafka_assets"
  title="assets.py — Kafka asset definitions"
/>

Other assets that depend on `raw_erp_events` or `raw_crm_events` will see them as materialized once the sensor triggers a run. Their presence in the asset graph makes the dependency explicit and enables downstream scheduling.

## The `DatabricksJobOrchestrator` component

The core reusable abstraction in this project is `DatabricksJobOrchestrator` — a custom <PyObject section="components" module="dagster" object="Component" /> that maps a Databricks job in a specific workspace to one or more Dagster assets.

Rather than writing a new `@asset` function for each workspace and job, you configure one YAML file per domain. Dagster's component system loads the YAML, instantiates the component, and calls `build_defs()` to produce the asset graph:

<CodeExample
  path="docs_projects/project_multi_workspace_databricks/src/project_multi_workspace_databricks/defs/customer_analytics_workspace/defs.yaml"
  language="yaml"
  title="defs/customer_analytics_workspace/defs.yaml"
/>

### How `build_defs` works

The `build_defs` method converts the component's configuration into a <PyObject section="definitions" module="dagster" object="Definitions" /> object containing a single <PyObject section="assets" module="dagster" object="multi_asset" decorator />. Each entry in `assets:` becomes an <PyObject section="assets" module="dagster" object="AssetSpec" />, carrying the asset key, group, dependencies, and Databricks metadata:

<CodeExample
  path="docs_projects/project_multi_workspace_databricks/src/project_multi_workspace_databricks/components/databricks_job_orchestrator.py"
  language="python"
  startAfter="start_build_defs"
  endBefore="end_build_defs"
  title="databricks_job_orchestrator.py — build_defs"
/>

When the multi-asset executes, it calls `execute()`, which uses `DatabricksClient` to trigger `jobs.run_now()` in the configured workspace and waits up to one hour for completion. On success, it yields a <PyObject section="assets" module="dagster" object="MaterializeResult" /> for each asset spec, attaching execution metadata (run ID, start/end times).

### Adding a new workspace

To add a new business domain, scaffold a new component instance:

```bash
dg scaffold defs \
  project_multi_workspace_databricks.components.databricks_job_orchestrator.DatabricksJobOrchestrator \
  new_workspace_name
```

This creates `defs/new_workspace_name/defs.yaml` pre-populated with the component schema. Fill in the `job_id`, `workspace_config`, and `assets` list — no Python code required.

## Configuration

### Databricks workspaces

Update `workspace_config` in each workspace's `defs.yaml` with real credentials:

```yaml
workspace_config:
  host: 'https://your-workspace.cloud.databricks.com'
  token: '${DATABRICKS_TOKEN}'
```

### Kafka

Update `KafkaResource` in `defs/core_assets/__init__.py`:

```python
KafkaResource(
    bootstrap_servers="your-kafka-broker:9092",
    topics=["erp-events", "crm-events"],
)
```

### Fivetran

The `salesforce_data` and `hubspot_data` assets are placeholder nodes — their materialization is driven externally by Fivetran connectors. To wire them to a real Fivetran instance, replace the `pass`-body assets with assets loaded from the Fivetran integration:

```python
from dagster_fivetran import FivetranResource, load_assets_from_fivetran_instance

fivetran_resource = FivetranResource(
    api_key=os.getenv("FIVETRAN_API_KEY"),
    api_secret=os.getenv("FIVETRAN_API_SECRET"),
)
```
