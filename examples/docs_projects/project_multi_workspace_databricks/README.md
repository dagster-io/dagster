# Multi-Workspace Databricks Example

A Dagster project demonstrating an enterprise data mesh architecture that orchestrates data pipelines across multiple Databricks workspaces, with Kafka for event-based ingestion, Fivetran for SaaS integrations, and Databricks Unity Catalog federation for accessing legacy SQL Server and PostgreSQL databases.

See the [full documentation](https://docs.dagster.io/examples/full-pipelines/multi-workspace-databricks) for a complete walkthrough.

## Getting started

```bash
git clone https://github.com/dagster-io/dagster.git
cd dagster/examples/docs_projects/project_multi_workspace_databricks
uv sync
uv run dg check defs
uv run dg dev
```

## Running tests

```bash
pytest tests/ -v
```
