---
title: Ingestion
description: Ingest Data from Goodreads
last_update:
  author: Dennis Hume
sidebar_position: 20
---

We will be working with a [Goodreads dataset](https://mengtingwan.github.io/data/goodreads#datasets) that consists of JSON files that contain different genres of books. The dataset consists of JSON files that contain different genres of books. We will focus on graphic novels to limit the amount of data we need to process. Within this domain, the files we need are `goodreads_books_comics_graphic.json.gz` and `goodreads_book_authors.json.gz`.

Since the data is normalized across these two files, we will want to combine them in some way to produce a single dataset. This is a great use case for [DuckDB](https://duckdb.org/). DuckDB is an in-process database, similar to SQLite, optimized for analytical workloads. Using DuckDB, we can directly load the semi-structured data and work on it using SQL.

We will start by creating two Dagster assets to load in the data. Each asset will load one of the files and create a DuckDB table (`graphic_novels` and `authors`). The asset will use the Dagster `DuckDBResource`, which gives us an easy way to interact with and run queries in DuckDB. Both files will create a table from their respective JSON files:

<CodeExample path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py" language="python" startAfter="start_graphic_novel" endBefore="end_graphic_novel"/>

Now that the base tables are loaded, we can move on to working with the data.

## Next steps

- Continue this example with [feature engineering](feature-engineering)