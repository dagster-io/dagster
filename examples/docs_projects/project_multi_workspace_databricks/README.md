# Multi-Workspace Databricks Example

A Dagster project demonstrating an enterprise data mesh architecture that orchestrates data pipelines across multiple Databricks workspaces, with Kafka for event-based ingestion, Fivetran for SaaS integrations, and Databricks Unity Catalog federation for accessing legacy SQL Server and PostgreSQL databases.

## Features

- **Multi-workspace Databricks orchestration**: A custom `DatabricksJobOrchestrator` component that declaratively configures assets produced by Databricks jobs across separate workspaces — each owned by a different business domain
- **Kafka event ingestion**: Sensor-based ingestion from Kafka topics with configurable batch processing and offset tracking
- **Fivetran SaaS integrations**: Asset definitions for Salesforce and HubSpot data synced via Fivetran
- **Legacy database federation**: Assets backed by SQL Server and PostgreSQL accessed via Databricks Unity Catalog Lakehouse Federation
- **Component-based YAML configuration**: Each Databricks workspace is configured via a `defs.yaml` file using the reusable `DatabricksJobOrchestrator` component

## Asset lineage

```
Raw Sources
├── Kafka (raw_erp_events, raw_crm_events)
├── Fivetran SaaS (salesforce_data, hubspot_data)
└── Legacy DBs (legacy_customer_data, legacy_transaction_data)
          │
          ▼
Workspace-Specific Transformations (via DatabricksJobOrchestrator)
├── customer_analytics/enriched_profiles
├── customer_analytics/customer_segments
├── sales_analytics/order_fulfillment
├── sales_analytics/revenue_forecasting
├── finance/invoice_reconciliation
├── finance/payment_tracking
├── finance/financial_statements
├── finance_2/customer_segments_aggregation
├── marketing/campaign_performance
├── marketing/attribution_model
└── marketing/customer_lifetime_value
          │
          ▼
Cross-Domain Analytics (core assets)
├── enriched_customer_profiles
├── order_fulfillment_status
├── customer_360_view
└── marketing_attribution
```

## Getting started

1. Clone the Dagster repository:

```bash
git clone https://github.com/dagster-io/dagster.git
cd dagster/examples/docs_projects/project_multi_workspace_databricks
```

2. Install dependencies:

```bash
uv sync
```

3. Configure credentials (see [Configuration](#configuration) below).

4. Validate the definitions load:

```bash
uv run dg check defs
```

5. Start the Dagster UI:

```bash
uv run dg dev
```

Open http://localhost:3000 in your browser to explore the asset graph and sensors.

## Configuration

### Databricks workspaces

Each workspace `defs.yaml` file requires a `workspace_config` with valid credentials:

```yaml
workspace_config:
  host: "https://your-workspace.cloud.databricks.com"
  token: "${DATABRICKS_TOKEN}"
```

### Kafka

Update the resource configuration in `defs/core_assets/__init__.py`:

```python
resources={
    "kafka_resource": KafkaResource(
        bootstrap_servers="your-kafka-broker:9092",
        group_id="dagster-consumer-group",
        topics=["erp-events", "crm-events"],
    ),
}
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

## Extending the example

### Adding a new Databricks workspace

Scaffold a new workspace configuration:

```bash
uv run dg scaffold defs \
  project_multi_workspace_databricks.components.databricks_job_orchestrator.DatabricksJobOrchestrator \
  new_workspace_name
```

Edit the generated `defs/new_workspace_name/defs.yaml` with your job ID, workspace credentials, and asset definitions.

### Adding more assets

Add new `@dg.asset` definitions to `assets.py` with the appropriate `group_name` and `deps`.

## Running tests

```bash
pytest tests/ -v
```
