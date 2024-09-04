---
title: Ingesting data with Dagster
description: Learn how to orchestrate data ingestion with Dagster
sidebar_position: 10
sidebar_label: Ingesting data
---

Dagster is often used to orchestrate the ingestion of data into a data warehouse or data lake, where it can be queried and transformed. Dagster integrates with several tools that are purpose-built for data ingestion, and it also enables writing custom code for ingesting data.

This guide covers how to use Dagster for data ingestion.

:::note
This guide focuses on batch data ingestion, as streaming data ingestion doesn't typically rely on an orchestrator to kick off or coordinate computations. However, streaming data assets can still be represented in Dagster for lineage purposes.
:::

## What you'll learn

- How Dagster helps with data ingestion
- How to integrate Dagster with different data ingestion tools
- How to write custom data ingestion pipelines

<details>
  <summary>Prerequisites</summary>
- Familiarity with [Assets](/concepts/assets)
</details>

## How Dagster helps with data ingestion

As a data orchestrator, Dagster helps with data ingestion as it can:

- **Automatically kick off computations that ingest data**, thus removing the need for manual intervention
- **Coordinate data ingestion with downstream data transformation,** such as rebuilding a set of dbt models after the upstream data they depend on is updated
- **Represent ingested data assets in an asset graph**, which enables understanding what ingested data exists, how ingested data is used, and where data is ingested from

## Orchestrating data ingestion tools

Dagster integrates with a variety of data ingestion tools, enabling you to sync diverse data sources into your data warehouse tables using pre-built connectors. With these integrations, Dagster allows you to:

- Represent ingested tables as assets within the Dagster asset graph
- Trigger asset materializations that automatically invoke these tools to initiate data syncs

Dagster currently integrates with the following data ingestion tools:

- [Airbyte](/todo)
- [dlt](/todo)
- [Fivetran](/todo)
- [Sling](/todo)

## Writing custom data ingestion pipelines

Writing code in a language like Python to ingest data into a platform is also a common approach. This is especially useful when you have unique data ingestion requirements that aren't addressed by existing tools, or when you prefer to keep your platform streamlined without adding new tools.

For example, imagine there's a CSV file of counties on the internet and you want to load it into your Snowflake data warehouse as a table. To do this, you might directly define an asset that represents that table in your warehouse. The asset's materialization function fetches data from the internet and loads it into that table:

<CodeExample filePath="guides/data-ingestion/custom-data-ingestion.py" language="python" title="Custom data ingestion" />

## Next steps

{/* TODO add next steps */}

- Learn how to [transform data using Dagster's dbt integration](/guides/ingestion-transformation/transform-dbt)
