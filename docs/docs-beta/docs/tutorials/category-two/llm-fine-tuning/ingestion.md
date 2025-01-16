---
title: Ingestion
description: Ingest Data from Goodreads
last_update:
  author: Dennis Hume
sidebar_position: 20
---

We will be working with data from Goodreads which can be found [here](https://mengtingwan.github.io/data/goodreads#datasets). The dataset consists of JSON files that contain different genres of books. We will focus on graphic novels to limit the amount of data we need to process. Within this domain, the files we need are `goodreads_books_comics_graphic.json.gz` and `goodreads_book_authors.json.gz`.

Since the data is normalized across these two files, we will want to combine them in some way to produce a single dataset. This is a great use case for [DuckDB](https://duckdb.org/). DuckDB is an in-process database, similar to SQLite, optimized for analytical workloads. Using DuckDB we can load the semi-structured data in directly and work on it using SQL.

We will start by creating two Dagster assets to load in the data. Each asset will load one of the files and create a DuckDB table (`graphic_novels` and `authors`). The asset will use the Dagster `DuckDBResource` which gives us an easy way to interact and run queries with DuckDB. Both files will create a table from their respective JSON files:

```python
@dg.asset(
    kinds={"duckdb"},
    description="Goodreads graphic novel data",
    group_name="ingestion",
    deps=[goodreads],
)
def graphic_novels(duckdb_resource: dg_duckdb.DuckDBResource):
    url = "https://datarepo.eng.ucsd.edu/mcauley_group/gdrive/goodreads/byGenre/goodreads_books_comics_graphic.json.gz"
    query = f"""
        create table if not exists graphic_novels as (
            select *
            from read_json(
                '{url}',
                ignore_errors = true
            )
        );
    """
    with duckdb_resource.get_connection() as conn:
        conn.execute(query)
```

Now that the base tables are loaded we can move onto working with the data.

## Next steps

- Continue this tutorial with [feature engineering](feature_engineering)