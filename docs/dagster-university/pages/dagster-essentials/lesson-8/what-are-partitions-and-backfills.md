---
title: 'Lesson 8: What are partitions and backfills?'
module: 'dagster_essentials'
lesson: '8'
---

# What are partitions and backfills?

Let's start by discussing what, exactly, partitions and backfills are.

---

## Partitions

Partitions are a way to split your data into smaller, easier-to-use chunks. By breaking the data into chunks, you get the following benefits:

- **Cost efficiency**: Run only the data that’s needed and gain granular control over slices. For example, you can store recent orders in hot storage and older orders in cheaper, cold storage.
- **Speed up compute**: Divide large datasets into smaller, more manageable parts to speed up queries.
- **Scalability**: As data grows, you can distribute it across multiple servers or storage systems or run multiple partitions at a time in parallel.
- **Concurrent processing**: Boost computational speed with parallel processing, significantly reducing the time and cost of data processing tasks.
- **Speed up debugging**: Test on an individual partition before trying to run larger ranges of data.

Partitions are a mental model and a physical representation. In the cookie orders example, orders are an asset. In our mental model and Dagster UI, there is only one `orders` asset regardless of how many days we partition the orders for. How it’s stored physically might differ. If we were to represent our cookie orders as a table in a database, it might be represented as a single `orders` table. However, if it’s dumped into Amazon Web Services (AWS) S3 as parquet files, creating a new parquet file per day/partition would better adhere to best practices.

In summary, partitions in Dagster enable you to compute on individual slices, but how it’s read or written from storage is flexible.

---

## Backfills

Backfilling is the process of running partitions for assets that either don’t exist or updating existing records.

Backfills are common when setting up a pipeline for the first time. The assets you want to materialize might have historical data that needs to be materialized to get the assets up to date. Another common reason to run a backfill is when you’ve changed the logic for an asset and need to update historical data with the new logic.
