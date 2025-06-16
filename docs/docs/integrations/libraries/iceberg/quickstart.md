---
title: Quickstart
description: Dagster supports saving and loading Iceberg tables as assets using I/O managers.
sidebar_position: 100
---

<p>{frontMatter.description}</p>

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need to:

- [Install `dagster-iceberg`](/integrations/libraries/iceberg#installation).
- [Create a temporary location for Iceberg and set up the catalog](https://py.iceberg.apache.org/#connecting-to-a-catalog).
- Create the `default` namespace:

  ```python
  catalog.create_namespace("default")
  ```

</details>

## Defining the I/O manager

To use an Iceberg I/O manager, add it to your <PyObject section="definitions" module="dagster" object="Definitions" />:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/iceberg/quickstart.py"
  startAfter="start_defining_the_io_manager"
  endBefore="end_defining_the_io_manager"
/>

## Storing a Dagster asset as an Iceberg table

The I/O manager will automatically persist the returned data to your warehouse:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/iceberg/quickstart.py"
  startAfter="start_storing_a_dagster_asset"
  endBefore="end_storing_a_dagster_asset"
/>

## Loading Iceberg tables in downstream assets

The I/O manager will also load the data stored in your warehouse when referenced in a dependent asset:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/iceberg/quickstart.py"
  startAfter="start_loading_iceberg_tables"
  endBefore="end_loading_iceberg_tables"
/>
