---
title: Ingesting data with Dagster
description: Learn how to ingest data into Dagster
sidebar_position: 10
sidebar_label: Ingesting data
---

This guide explains how to use Dagster to orchestrate the ingestion of data into a data warehouse or data lake, where it can be queried and transformed. Dagster integrates with several tools that are purpose-built for data ingestion, and it also enables writing custom code for ingesting data.

A data platform typically centers on a small number of data warehouses or object stores, where data is consolidated in standard formats for reporting, transformation, and analysis. The data inside the platform often comes from a large and diverse set of sources, such as application logs, customer relationship management (CRM) software, spreadsheets, public data sources available on the internet, and more. Data ingestion is the process of extracting data from these sources to loading it into the data platform. Data ingestion makes up the "E" and "L" in the "ELT" paradigm (extract-load-transform).

## What you'll learn

- How Dagster helps with data ingestion
- How Dagster relates to different technologies and paradigms for data ingestion
- How to get started using Dagster to ingest data using your preferred technology and paradigm

<details>
  <summary>Prerequisites</summary>
- Familiarity with [asset definitions](/concepts/assets)
</details>

## How Dagster helps with data ingestion

As a data orchestrator, Dagster helps with data ingestion in the following ways:
- It can automatically kick off computations that ingest data.
- It can coordinate data ingestion with downstream data transformation, for example to rebuild a set of dbt models after the upstream data they depend on is updated.
- It can represent ingested data assets in its data asset graph, which enables understanding what ingested data exists, how ingested data is used, and where data is ingested from.

### Batch vs. streaming data ingestion

There are two main paradigms for data ingestion: batch and streaming. With batch data ingestion, data is moved in discrete batches. With streaming data ingestion, data continuously flows in.

Dagster has a different relationship to streaming data ingestion than it does to batch data ingestion. For batch data ingestion, Dagster often takes responsibility for kicking off the computations to ingest the batches of data, either at a regular cadence or when it discovers that new data is available in the source system.

For streaming data ingestion, Dagster doesn't orchestrate the data ingestion, but still often represents the ingested data assets in its asset graph. Dagster can hold metadata about these assets, represent the lineage between them and downstream assets, and automatically kick off computations to observe them.

## Orchestrate a data ingestion tool

Dagster integrates with several tools that are purpose-built for data ingestion. These tools roughly fall into two main categories:
- Hosted data ingestion services.
- Embeddable data ingestion libraries.

### Hosted data ingestion services

Dagster provides two integrations with two hosted data ingestion services: Fivetran and Airbyte.

With a hosted data ingestion service, the set of data sources to ingest into the data platform is defined inside the service. Dagster's integrations with these services invoke their REST APIs to find out about the set of data assets that they ingest and load those asset definitions into Dagster's asset graph. The "materialize" action on these Dagster asset definitions invokes REST APIs provided by these services to ingest the latest data from the source.

To learn how to use Dagster to orchestrate a hosted data ingestion service, follow the link for that service above.

### Embeddable data ingestion libraries

With an embeddable data ingestion library, the set of data sources to ingest into the data platform is defined using files that are typically managed inside the same git repository as other Dagster pipelines. Dagster's integrations with these libraries invokes them to interpret these files and load the data assets defined in them into Dagster's asset graph. The "materialize" action on these Dagster asset definitions invokes the library to ingest the latest data from the source.

Dagster provides two integrations with embeddable data ingestion libraries: Sling and DLT.

To learn how to use Dagster to orchestrate a hosted data ingestion service, follow the link for that library above.

## Write a custom data ingestion pipeline

It's also common to write code in a language like Python to ingest data into a data platform.

For example, if there's a CSV file on the internet of counties, and you want to load it into your Snowflake data warehouse as a table, you might directly define an asset that represents that table in your warehouse. The asset's materialization function fetches data from the internet and loads it into that table.

```python
@asset
def counties(snowflake: SnowflakeResource) -> None:
    # TODO
    data = fetch_some_data()
    snowflake.conn.execute("INSERT INTO ...")
```
