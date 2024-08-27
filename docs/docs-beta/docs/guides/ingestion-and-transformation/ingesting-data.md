---
title: Ingesting data with Dagster
description: Learn how to orchestrate data ingestion with Dagster
sidebar_position: 10
sidebar_label: Ingesting data
---

Dagster is often used to orchestrate the ingestion of data into a data warehouse or data lake, where it can be queried and transformed. Dagster integrates with several tools that are purpose-built for data ingestion, and it also enables writing custom code for ingesting data.

This guide explains how to use Dagster for data ingestion.

**Note**: This guide focuses on batch data ingestion, because streaming data ingestion doesn't typically rely on an orchestrator to kick off or coordinate computations. However, streaming data assets can still be represented in Dagster for lineage purposes.

## What you'll learn

- How Dagster helps with data ingestion
- How to integrate Dagster with different data ingestion tools
- How to write custom data ingestion pipelines

<details>
  <summary>Prerequisites</summary>
- Familiarity with [asset definitions](/concepts/assets)
</details>

## How Dagster helps with data ingestion

As a data orchestrator, Dagster helps with data ingestion in the following ways:
- It can automatically kick off computations that ingest data.
- It can coordinate data ingestion with downstream data transformation, for example to rebuild a set of dbt models after the upstream data they depend on is updated.
- It can represent ingested data assets in its data asset graph, which enables understanding what ingested data exists, how ingested data is used, and where data is ingested from.

## Orchestrate a data ingestion tool

Dagster integrates with several data ingestion tools. These tools allow using pre-built syncs to bring diverse data sources into data warehouse tables. Dagster's integrations with these tools help you:
- Represent the ingested tables as assets in the Dagster asset graph.
- Kick off asset materializations that invoke these tools to trigger syncs.

Dagster provides four integrations with data ingestion tools:
- Fivetran
- Airbyte
- Sling
- DLT

## Write a custom data ingestion pipeline

It's also common to write code in a language like Python to ingest data into a data platform. This is useful when you have specific data ingestion needs that aren't covered by an existing tool, or if you don't want to introduce new tools into your platform.

For example, if there's a CSV file on the internet of counties, and you want to load it into your Snowflake data warehouse as a table, you might directly define an asset that represents that table in your warehouse. The asset's materialization function fetches the file from the internet and loads it into that table.

<CodeExample filePath="guides/data-ingestion/custom-data-ingestion.py" language="python" title="Custom data ingestion" />
