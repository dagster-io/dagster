---
title: Ingesting data with Dagster
description: Learn how to orchestrate data ingestion with Dagster
sidebar_position: 10
sidebar_label: Ingest data
---

import { Card, CardGroup } from '@site/src/components/Cards';

:::note
This guide focuses on batch data ingestion, as streaming data ingestion doesn't typically rely on an orchestrator to kick off or coordinate computations. However, streaming data assets can still be represented in Dagster for lineage purposes.
:::

Dagster is often used to orchestrate the ingestion of data into a data warehouse or data lake, where it can be queried and transformed. Dagster integrates with several tools that are purpose-built for data ingestion, and it also enables writing custom code for ingesting data.

<details>
<summary>Prerequisites</summary>

To follow this guide, you'll need:

- Familiarity with [Assets](/concepts/assets)
</details>

## How Dagster supports data ingestion

As a data orchestrator, Dagster helps with data ingestion as it can:

- **Automatically kick off computations that ingest data**, thus removing the need for manual intervention
- **Coordinate data ingestion with downstream data transformation,** such as rebuilding a set of dbt models after the upstream data they depend on is updated
- **Represent ingested data assets in an asset graph**, which enables understanding what ingested data exists, how ingested data is used, and where data is ingested from

## Orchestrating data ingestion tools

Dagster integrates with a variety of data ingestion tools, enabling you to sync diverse data sources into data warehouse tables using pre-built connectors. With these integrations, Dagster allows you to:

- Represent ingested tables as assets within the Dagster asset graph
- Trigger asset materializations that automatically invoke these tools to initiate data syncs

Dagster currently integrates with the following data ingestion tools:

- Airbyte
- dlt
- Fivetran
- Sling

## Writing custom data ingestion pipelines

Using a language like Python to write code for data ingestion into a platform is also a common approach. This is useful when you have unique data ingestion requirements that aren't addressed by existing tools, or when you prefer to keep your platform streamlined without adding new tools.

For example, imagine there's a CSV file of counties on the internet and you want to load it into your Snowflake data warehouse as a table. To do this, you might define a Dagster asset that represents that table in your warehouse. The asset's materialization function fetches data from the internet and loads it into that table:

<CodeExample filePath="guides/data-ingestion/custom-data-ingestion.py" language="python" />

## Next steps

- Transform data using [Dagster's dbt integration](/guides/transform-dbt)
- Run non-Python code with [Dagster Pipes](/guides/non-python)