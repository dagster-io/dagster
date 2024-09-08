---
title: "Create a pipeline"
description: "Learn how to create data pipelines using Dagster's asset-based approach"
---

In Dagster, data pipelines are created using an asset-based approach. This overview will introduce you to the key concepts and steps involved in building a Dagster pipeline.

## What you'll learn

- The basics of Dagster's asset-based pipelines
- How to define and connect data assets
- Ways to enhance your pipeline with metadata and partitioning
- How to integrate external data sources

<details>
  <summary>Prerequisites</summary>

Before continuing, you should be familiar with:

- [Installing Dagster](/tutorial/installation)
- [The Quickstart Tutorial](/tutorial/quick-start)

</details>

Dagster uses software-defined assets as the building blocks of data pipelines. An asset represents a data object, such as a table, file, or machine learning model, that your pipeline produces or updates.

As you define multiple assets and their dependencies, Dagster automatically creates an asset graph. This graph represents the structure and flow of your data pipeline. These nodes are not the individual operations that create the assets, but rather the assets themselves.

```mermaid
flowchart LR
    A[Raw Sales Data] --> B[Cleaned Sales Data]
    A -.-> C([Data Quality Checks])
    B --> D[Sales Aggregations]
    C --> D
    D --> E[Customer Segmentation]
    D --> F[Sales Dashboard]
    E --> G[Lead Scoring Model]
```

## Steps to create a pipeline

Most Dagster pipelines follow these steps:

1. **Define data assets**: Start by creating individual assets using the `@asset` decorator. Each asset represents a data object in your pipeline.

2. **Create dependencies**: Connect your assets by specifying dependencies, allowing Dagster to understand the flow of data through your pipeline.

3. **Enrich with metadata**: Add context and improve observability by enriching your assets with metadata, such as descriptions, owners, and data quality checks.

4. **Partition your data**: For large datasets or time-based processing, use Dagster's partitioning feature to efficiently manage and process your data.

5. **Represent external sources**: Integrate external data sources into your pipeline to create a comprehensive view of your data ecosystem.

## Next steps

To start building your Dagster pipeline, dive into the following guides:

- [Define data assets](/guides/dagster/define-data-assets)
- [Create dependencies between assets](/guides/dagster/create-asset-dependencies)
- [Enrich assets with metadata](/guides/dagster/enrich-assets-with-metadata)
- [Partition assets](/guides/dagster/partition-assets)
- [Represent external data sources](/guides/dagster/represent-external-data-sources)

By following these guides, you'll learn how to create powerful, maintainable data pipelines using Dagster's asset-based approach.
