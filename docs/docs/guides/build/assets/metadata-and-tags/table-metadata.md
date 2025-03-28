---
title: "Table metadata"
description: "Table metadata can be used to provide additional context about a tabular asset, such as its schema, row count, and more."
sidebar_position: 3000
---

Table metadata provides additional context about a tabular asset, such as its schema, row count, and more. This metadata can be used to improve collaboration, debugging, and data quality in your data platform.

Dagster supports attaching different types of table metadata to assets, including:

- [**Column schema**](#attaching-column-schema), which describes the structure of the table, including column names and types
- [**Row count**](#attaching-row-count), which describes the number of rows in a materialized table
- [**Column-level lineage**](#attaching-column-level-lineage), which describes how a column is created and used by other assets

## Attaching column schema

### For assets defined in Dagster

Column schema metadata can be attached to Dagster assets either as [definition metadata](index.md#definition-time-metadata) or [runtime metadata](index.md#runtime-metadata), which will then be visible in the Dagster UI. For example:

![Column schema for an asset in the Dagster UI](/images/guides/build/assets/metadata-tags/metadata-table-schema.png)

If the schema of your asset is pre-defined, you can attach it as definition metadata. If the schema is only known when an asset is materialized, you can attach it as metadata to the materialization.

To attach schema metadata to an asset, you will need to:

1. Construct a <PyObject section="metadata" module="dagster" object="TableSchema"/> object with <PyObject section="metadata" module="dagster" object="TableColumn"  /> entries describing each column in the table
2. Attach the `TableSchema` object to the asset as part of the `metadata` parameter under the `dagster/column_schema` key. This can be attached to your asset definition, or to the <PyObject section="assets" module="dagster" object="MaterializeResult" /> object returned by the asset function.

Below are two examples of how to attach column schema metadata to an asset, one as definition metadata and one as runtime metadata:

<CodeExample path="docs_snippets/docs_snippets/concepts/metadata-tags/asset_column_schema.py" />

The schema for `my_asset` will be visible in the Dagster UI.

### For assets loaded from integrations

Dagster's dbt integration enables automatically attaching column schema metadata to assets loaded from dbt models. For more information, see the [dbt documentation](/integrations/libraries/dbt/reference#fetching-column-level-metadata).

## Attaching row count

Row count metadata can be attached to Dagster assets as [runtime metadata](index.md#runtime-metadata) to provide additional context about the number of rows in a materialized table. This will be highlighted in the Dagster UI. For example:

![Row count for an asset in the Dagster UI](/images/guides/build/assets/metadata-tags/metadata-row-count.png)

In addition to showing the latest row count, Dagster will let you track changes in the row count over time, and you can use this information to monitor data quality.

To attach row count metadata to an asset, you will need to attach a numerical value to the `dagster/row_count` key in the metadata parameter of the <PyObject section="assets" module="dagster" object="MaterializeResult" /> object returned by the asset function. For example:

<CodeExample path="docs_snippets/docs_snippets/concepts/metadata-tags/asset_row_count.py" />

## Attaching column-level lineage

Column lineage enables data and analytics engineers alike to understand how a column is created and used in your data platform. For more information, see the [column-level lineage documentation](/guides/build/assets/metadata-and-tags/column-level-lineage).

## Ensuring table schema consistency

When column schemas are defined at runtime through runtime metadata, it can be helpful to detect and alert on schema changes between materializations. Dagster provides <PyObject section="asset-checks" module="dagster" object="build_column_schema_change_checks"/> API to help detect these changes.

This function creates asset checks which compare the current materialization's schema against the schema from the previous materialization. These checks can detect:

- Added columns
- Removed columns
- Changed column types

Let's define a column schema change check for our asset from the example above that defines table schema at runtime, `my_other_asset`.

<CodeExample path="docs_snippets/docs_snippets/concepts/metadata-tags/schema_change_checks.py" startAfter="start_check" endBefore="end_check" />
