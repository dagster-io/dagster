# project_atproto_dashboard

An end-to-end demonstration of ingestion data from the ATProto API, modeling it with dbt, and presenting it with Power BI.

![Architecture Diagram](_static/architecture-diagram.png)

![Project asset lineage](_static/lineage.svg)

## Features used

1. Ingestion of data-related Bluesky posts
   - Dynamic partitions
   - Declarative automation
   - Concurrency limits
2. Modelling data using _dbt_
3. Representing data in a dashboard

## Getting started

### Environment Setup

Ensure the following environments have been populated in your `.env` file. Start by copying the
template.

```
cp .env.example .env
```

And then populate the fields.

### Development

Generate the dbt project manifest:

    cd dbt_project
    uv run dbt build

Install the project dependencies:

    uv venv

    source .venv/bin/activate

    uv pip install -e ".[dev]"

Start Dagster:

    dg dev

## Resources

- https://docs.bsky.app/docs/tutorials/viewing-feeds
- https://docs.bsky.app/docs/advanced-guides/rate-limits
- https://atproto.blue/en/latest/atproto_client/auth.html#session-string
- https://tenacity.readthedocs.io/en/latest/#waiting-before-retrying
