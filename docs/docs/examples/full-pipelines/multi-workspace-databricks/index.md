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
       ```bash source .venv/bin/activate ```
     </TabItem>
     <TabItem value="windows" label="Windows">
       ```bash .venv\Scripts\activate ```
     </TabItem>
   </Tabs>

4. Configure credentials for your Databricks workspaces and Kafka broker (see [Configuration](#configuration) below).

## Step 2: Launch the Dagster webserver

Start the Dagster webserver from the project root:

```bash
dg dev
```

Open http://localhost:3000 in your browser. You'll see 21 assets across seven groups — the full data mesh from raw ingestion through analytics.

## Architecture

The project is organized into two layers:

### Core assets (`defs/core_assets/`)

Defined as standard `@asset` functions, these represent the shared data foundation:

| Group            | Assets                                                                                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `ingestion`      | `raw_erp_events`, `raw_crm_events`, `salesforce_data`, `hubspot_data`, `legacy_customer_data`, `legacy_transaction_data` |
| `transformation` | `enriched_customer_profiles`, `order_fulfillment_status`                                                                 |
| `analytics`      | `customer_360_view`, `marketing_attribution`                                                                             |

Two Kafka sensors (`watch_kafka_replica_0`, `watch_kafka_replica_1`) poll for ERP and CRM events and trigger runs against the raw ingestion assets.

### Workspace assets (`defs/*/defs.yaml`)

Each of the four business domains is configured via a `defs.yaml` file using the reusable `DatabricksJobOrchestrator` component:

| Workspace               | Databricks job | Assets produced                                                                                       |
| ----------------------- | -------------- | ----------------------------------------------------------------------------------------------------- |
| `customer_analytics`    | Job 12345      | `enriched_profiles`, `customer_segments`                                                              |
| `sales_analytics`       | Job 12346      | `order_fulfillment`, `revenue_forecasting`                                                            |
| `finance_reporting`     | Job 12347      | `invoice_reconciliation`, `payment_tracking`, `financial_statements`, `customer_segments_aggregation` |
| `marketing_attribution` | Job 12348      | `campaign_performance`, `attribution_model`, `customer_lifetime_value`                                |

### Asset lineage

```
Raw Sources
├── Kafka (raw_erp_events, raw_crm_events)
├── Fivetran SaaS (salesforce_data, hubspot_data)
└── Legacy DBs (legacy_customer_data, legacy_transaction_data)
          │
          ▼
Workspace-Specific Transformations
├── customer_analytics/enriched_profiles
├── customer_analytics/customer_segments
├── sales_analytics/order_fulfillment
├── sales_analytics/revenue_forecasting
├── finance/invoice_reconciliation → finance/financial_statements
└── marketing/campaign_performance → marketing/attribution_model
          │
          ▼
Cross-Domain Analytics
├── customer_360_view
└── marketing/customer_lifetime_value
```

## The `DatabricksJobOrchestrator` component

The core reusable abstraction in this project is `DatabricksJobOrchestrator` — a custom `dg.Component` that maps a Databricks job to one or more Dagster assets. Each workspace `defs.yaml` is an instance of this component:

```yaml
type: project_multi_workspace_databricks.components.databricks_job_orchestrator.DatabricksJobOrchestrator

attributes:
  job_id: 12345
  workspace_config:
    host: 'https://your-workspace.cloud.databricks.com'
    token: '${DATABRICKS_TOKEN}'
  assets:
    - key: 'customer_analytics/enriched_profiles'
      description: 'Customer profiles enriched with transaction history'
      group_name: 'customer_analytics'
      deps:
        - 'raw_erp_events'
        - 'legacy_customer_data'
```

To add a new workspace, scaffold a new component instance:

```bash
dg scaffold defs \
  project_multi_workspace_databricks.components.databricks_job_orchestrator.DatabricksJobOrchestrator \
  new_workspace_name
```

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

Configure the helper in `assets.py` with your API credentials:

```python
from dagster_fivetran import FivetranResource, load_assets_from_fivetran_instance

fivetran_resource = FivetranResource(
    api_key=os.getenv("FIVETRAN_API_KEY"),
    api_secret=os.getenv("FIVETRAN_API_SECRET"),
)
```
