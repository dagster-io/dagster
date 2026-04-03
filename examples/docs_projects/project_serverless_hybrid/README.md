# Dagster+ Serverless & Hybrid Example

This example demonstrates deploying both **Dagster+ Serverless** and **Dagster+ Hybrid** code locations from a single repository.

- **Serverless location**: Lightweight API ingestion and DuckDB analytics
- **Hybrid location**: Heavy ML workloads routed to a dedicated agent queue

See the [documentation](https://docs.dagster.io/deployment/dagster-plus/management/serverless-hybrid-deployment) for a full walkthrough.

## Local development

```bash
# Serverless location
cd code_locations/serverless-location
uv sync
uv run dg dev

# Hybrid location
cd code_locations/hybrid-location
uv sync
uv run dg dev
```
