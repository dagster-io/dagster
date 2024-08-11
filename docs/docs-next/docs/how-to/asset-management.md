---
title: Asset Management
description: Learn how to manage assets in Dagster
last_update: 
    date: 2024-08-10
    author: Pedram Navid
---

In Dagster, assets are the building blocks of data pipelines. They represent the data that is being processed by the pipeline.
An asset can represent a table in a database, a file in a file system, or even a machine learning model or notebook.


## How to create an asset

In Dagster, you typically define an asset using the `@asset` decorator. 

```python
from dagster import asset

@asset
def my_asset():
    return "Hello, World!"
```

Assets can perform actions in external systems, such as loading data from a database, writing data to a file, or training a machine learning model.

```python
from dagster import asset
import duckdb

@asset
def my_asset():
    with duckdb.connect("file.db") as con:
        con.sql("CREATE TABLE test (i INTEGER)")
        con.sql("INSERT INTO test VALUES (42)")
        con.table("test").show()
        
```
